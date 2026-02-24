"""
agent/summarizer.py

Conversation summarizer — converts long conversations into memory records
using LLMClient.

Summary record format:
    {
        "summary": str,
        "key_topics": list[str],
        "emotional_tone": str,
        "importance_score": float,   # 0.0 - 1.0
        "timestamp": str,            # ISO 8601
    }
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Default summarization system instruction
_DEFAULT_SYSTEM = (
    "You are a conversation memory assistant. "
    "Analyze the given conversation and summarize it in JSON format. "
    "JSON keys: summary (str), key_topics (list[str]), "
    "emotional_tone (str), importance_score (float 0-1). "
    "Output only valid JSON, nothing else."
)


class ConversationSummarizer:
    """
    Summarizes conversation history using an LLM.

    Parameters:
        llm_client: LLMClient instance
        system_prompt: Custom system instruction (optional)
        max_tokens: Maximum tokens for the summary
        min_messages: Minimum number of messages required for summarization
    """

    def __init__(
        self,
        llm_client,
        system_prompt: Optional[str] = None,
        max_tokens: int = 512,
        min_messages: int = 4,
    ) -> None:
        self.llm = llm_client
        self.system_prompt = system_prompt or _DEFAULT_SYSTEM
        self.max_tokens = max_tokens
        self.min_messages = min_messages

    def summarize(self, messages: list[dict], identity_context: Optional[str] = None) -> dict:
        """
        Summarize a message list and return it as a memory record.

        Parameters:
            messages: [{"role": str, "content": str}] list
            identity_context: Person identity information (optional)

        Returns:
            dict: Memory record
        """
        if len(messages) < self.min_messages:
            logger.debug("Not enough messages for summarization (%d < %d)", len(messages), self.min_messages)
            return self._empty_record()

        prompt = self._build_prompt(messages, identity_context)
        try:
            raw = self.llm.complete(prompt, system_prompt=self.system_prompt, max_tokens=self.max_tokens, temperature=0.3)
            record = self._parse_response(raw)
            record["timestamp"] = datetime.now(timezone.utc).isoformat()
            record["message_count"] = len(messages)
            logger.info("Conversation summary created: %d messages, importance=%.2f", len(messages), record.get("importance_score", 0.0))
            return record
        except Exception as e:
            logger.error("Summarization error: %s", e)
            return self._empty_record()

    def should_summarize(self, messages: list[dict], threshold: int = 20) -> bool:
        """
        Check whether the conversation history has exceeded the summarization threshold.

        Parameters:
            messages: Current message list
            threshold: Message count threshold for summarization

        Returns:
            bool: Whether summarization should be performed
        """
        return len(messages) >= threshold

    def extract_key_facts(self, messages: list[dict]) -> list[str]:
        """
        Extract important facts from the conversation.

        Returns:
            list[str]: List of important facts
        """
        if not messages:
            return []

        system = (
            "Extract important facts, preferences, and personal information from the conversation. "
            "Write one fact per line. Write only facts, no commentary."
        )
        prompt = self._format_messages(messages)
        try:
            raw = self.llm.complete(prompt, system_prompt=system, max_tokens=256, temperature=0.2)
            facts = [line.strip() for line in raw.splitlines() if line.strip()]
            return facts
        except Exception as e:
            logger.error("Fact extraction error: %s", e)
            return []

    # Helper methods

    def _build_prompt(self, messages: list[dict], identity_context: Optional[str]) -> str:
        parts = []
        if identity_context:
            parts.append(f"Identity context: {identity_context}\n")
        parts.append("Summarize the following conversation:\n\n")
        parts.append(self._format_messages(messages))
        return "".join(parts)

    @staticmethod
    def _format_messages(messages: list[dict]) -> str:
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    @staticmethod
    def _parse_response(raw: str) -> dict:
        raw = raw.strip()
        # Strip markdown code blocks
        if raw.startswith("```"):
            lines = raw.splitlines()
            raw = "\n".join(lines[1:-1]) if len(lines) > 2 else raw
        try:
            data = json.loads(raw)
            return {
                "summary": str(data.get("summary", "")),
                "key_topics": list(data.get("key_topics", [])),
                "emotional_tone": str(data.get("emotional_tone", "neutral")),
                "importance_score": float(data.get("importance_score", 0.5)),
            }
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning("JSON parse error, using raw text: %s", e)
            return {
                "summary": raw,
                "key_topics": [],
                "emotional_tone": "unknown",
                "importance_score": 0.5,
            }

    @staticmethod
    def _empty_record() -> dict:
        return {
            "summary": "",
            "key_topics": [],
            "emotional_tone": "neutral",
            "importance_score": 0.0,
            "message_count": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
