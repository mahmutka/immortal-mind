"""
agent/memory_manager.py

Memory coordinator — read/write operations integrated with CognitioEngine.

Responsibilities:
    - Promoting from short-term memory to long-term memory
    - Fetching relevant memories via semantic search
    - Periodically summarizing conversation history
    - Preserving identity consistency
"""

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Default configuration values
_DEFAULT_SHORT_TERM_LIMIT = 20       # short-term memory window (message count)
_DEFAULT_LONG_TERM_THRESHOLD = 0.6   # minimum importance score for writing to long-term memory
_DEFAULT_RECALL_LIMIT = 5            # single-shot recall limit


class MemoryManager:
    """
    Memory read/write coordinator.

    Communicates with CognitioEngine and works together with the summarizer.

    Parameters:
        cognitio: CognitioEngine instance (or compatible interface)
        summarizer: ConversationSummarizer instance (optional)
        identity_id: Active identity UUID
        config: Additional configuration
    """

    def __init__(
        self,
        cognitio=None,
        summarizer=None,
        identity_id: Optional[str] = None,
        config: Optional[dict] = None,
    ) -> None:
        self.cognitio = cognitio
        self.summarizer = summarizer
        self.identity_id = identity_id
        self.config = config or {}

        self._short_term: list[dict] = []
        self._short_term_limit: int = self.config.get("short_term_limit", _DEFAULT_SHORT_TERM_LIMIT)
        self._long_term_threshold: float = self.config.get("long_term_threshold", _DEFAULT_LONG_TERM_THRESHOLD)
        self._recall_limit: int = self.config.get("recall_limit", _DEFAULT_RECALL_LIMIT)
        self._last_time_flush: float = time.monotonic()
        self._time_flush_interval: float = float(self.config.get("time_flush_interval_seconds", 600))
        self._flush_lock = threading.Lock()

        logger.info("MemoryManager ready: identity_id=%s", self.identity_id)

    # Short-Term Memory

    def add_message(self, role: str, content: str) -> None:
        """
        Adds a message to short-term memory.

        Automatically triggers summarization when the window threshold is reached.

        Parameters:
            role: "user" or "assistant"
            content: Message content
        """
        self._short_term.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        logger.debug("Added to short-term memory: role=%s, length=%d", role, len(self._short_term))

        if len(self._short_term) >= self._short_term_limit:
            with self._flush_lock:
                if len(self._short_term) >= self._short_term_limit:
                    self._flush_to_long_term()

    def get_recent_messages(self, limit: Optional[int] = None) -> list[dict]:
        """
        Returns the last N messages (without timestamp, pure message format).

        Parameters:
            limit: Maximum number of messages to return

        Returns:
            list[dict]: [{"role": str, "content": str}] list
        """
        msgs = self._short_term if limit is None else self._short_term[-limit:]
        return [{"role": m["role"], "content": m["content"]} for m in msgs]

    def clear_short_term(self) -> None:
        """Clears short-term memory."""
        self._short_term.clear()
        logger.debug("Short-term memory cleared.")

    def time_based_flush(self) -> bool:
        """
        Time-based flush: triggers a flush if enough time has passed since
        the last flush and there are messages in short-term memory.

        Called periodically by the background timer thread.

        Returns:
            bool: Whether a flush occurred
        """
        now = time.monotonic()
        elapsed = now - self._last_time_flush
        if elapsed >= self._time_flush_interval and self._short_term:
            with self._flush_lock:
                # Re-check under lock — another thread may have already flushed
                if time.monotonic() - self._last_time_flush < self._time_flush_interval:
                    return False
                logger.info(
                    "Time-based flush triggered (%.0f seconds elapsed, %d messages pending)",
                    elapsed,
                    len(self._short_term),
                )
                self._flush_to_long_term()
                self._last_time_flush = time.monotonic()
            return True
        return False

    # Long-Term Memory

    def recall(self, query: str, limit: Optional[int] = None) -> list[dict]:
        """
        Retrieves relevant memories via semantic query.

        Parameters:
            query: Search query
            limit: Maximum number of results

        Returns:
            list[dict]: List of memory records
        """
        if self.cognitio is None:
            logger.warning("CognitioEngine not connected, recall will not work.")
            return []

        limit = limit or self._recall_limit
        try:
            results = self.cognitio.retrieve_memories(context=query, top_k=limit)
            memories = []
            for record, score in results:
                memories.append({
                    "summary": record.content,
                    "key_topics": record.tags,
                    "timestamp": record.created_at.isoformat(),
                    "importance_score": float(score),
                    "memory_type": record.memory_type.value,
                })
            logger.debug("Recall: %d memories retrieved (query=%s)", len(memories), query[:40])
            return memories
        except Exception as e:
            logger.error("Recall error: %s", e)
            return []

    def store(self, record: dict) -> Optional[str]:
        """
        Writes a record to long-term memory.

        Parameters:
            record: Memory record (dict containing summary, key_topics, etc.)

        Returns:
            str | None: Interaction ID or None (on error)
        """
        if self.cognitio is None:
            logger.warning("CognitioEngine not connected, store will not work.")
            return None

        importance = record.get("importance_score", 0.0)
        if importance < self._long_term_threshold:
            logger.debug("Importance score below threshold (%.2f < %.2f), skipping.", importance, self._long_term_threshold)
            return None

        summary = record.get("summary", "")
        if not summary:
            return None

        try:
            result = self.cognitio.process_interaction(
                role="assistant",
                content=summary,
                emotional_tone=float(record.get("emotional_intensity", 0.0)),
            )
            memory_id = result.get("interaction_id")
            logger.info("Written to long-term memory: memory_id=%s, importance=%.2f", memory_id, importance)
            return memory_id
        except Exception as e:
            logger.error("Memory write error: %s", e)
            return None

    def load_identity_context(self) -> dict:
        """
        Loads identity profile and past summaries.

        Returns:
            dict: Identity context (cognitive state + personality)
        """
        if self.cognitio is None:
            return {}

        try:
            context = self.cognitio.get_cognitive_state()
            logger.debug("Identity context loaded: identity_id=%s", self.identity_id)
            return context or {}
        except Exception as e:
            logger.error("Identity context could not be loaded: %s", e)
            return {}

    def build_context_string(self, query: str) -> str:
        """
        Builds context text from memory records related to the query.

        Parameters:
            query: User message or search query

        Returns:
            str: Context text that can be added to the system prompt
        """
        memories = self.recall(query)
        if not memories:
            return ""

        parts = ["[Relevant Memories]"]
        for i, mem in enumerate(memories, 1):
            summary = mem.get("summary", "")
            topics = ", ".join(mem.get("key_topics", []))
            ts = mem.get("timestamp", "")[:10]
            parts.append(f"{i}. [{ts}] {summary} (Topics: {topics})")
        return "\n".join(parts)

    # Internal methods

    def _flush_to_long_term(self) -> None:
        """Summarize short-term memory and transfer to long-term."""
        if self.summarizer is None:
            logger.debug("No summarizer, skipping flush.")
            self._short_term = self._short_term[-10:]
            return

        logger.info("Short-term memory reached threshold, summarizing...")
        record = self.summarizer.summarize(
            self._short_term,
            identity_context=str(self.identity_id),
        )
        memory_id = self.store(record)
        if memory_id:
            # Keep last 10 messages
            self._short_term = self._short_term[-10:]
            logger.info("Flush complete: memory_id=%s", memory_id)
        else:
            logger.warning("Memory could not be saved during flush.")

    def get_stats(self) -> dict[str, Any]:
        """Returns memory statistics."""
        return {
            "short_term_count": len(self._short_term),
            "short_term_limit": self._short_term_limit,
            "identity_id": self.identity_id,
            "cognitio_connected": self.cognitio is not None,
            "summarizer_connected": self.summarizer is not None,
        }
