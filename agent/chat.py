"""
agent/chat.py

Terminal chat loop — the main interface for the Immortal Mind Protocol.

Usage:
    python -m agent.chat
    python -m agent.chat --provider groq
    python -m agent.chat --provider ollama --identity identity-uuid

Commands (during chat):
    /quit or /exit  : Exit
    /clear          : Clear conversation history
    /memory         : Show memory statistics
    /provider       : Active provider info
    /help           : Help
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import logging
import os
import sys
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)

_MAX_INPUT_LENGTH = 32_768  # 32KB — prevent memory/DoS via oversized inputs
_KS_RATE_LIMIT = 50        # max kill switch checks before throttle kicks in
_KS_THROTTLE_SLEEP = 2.0   # seconds to sleep when rate limit is hit

# PBKDF2-HMAC-SHA256 for kill switch passphrase — must match cognitio/engine.py constants
_KS_PBKDF2_SALT = b"IMP-kill-switch-salt-v1"
_KS_PBKDF2_ITER = 100_000


def _hash_kill_switch(passphrase: str) -> str:
    """Derive a secure hash from a kill switch passphrase using PBKDF2-HMAC-SHA256."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        passphrase.encode("utf-8"),
        _KS_PBKDF2_SALT,
        _KS_PBKDF2_ITER,
    ).hex()

_BANNER = r"""
  ___                           _        _   __  __ _           _
 |_ _|_ __ ___  _ __ ___   ___ _ __| |_ __ _| | |  \/  (_)_ __   __| |
  | || _ _ \ | _ _ \ / _ \| _ __| __/ _` | | | |\/| | | _ \ / _` |
  | || | | | | | | | | | (_) | |  | || (_| | | | |  | | | | | | (_| |
 |___|_| |_|_|_| |_|_|\___/|_|   \__\__,_|_| |_|  |_|_|_| |_|\__,_|

  Immortal Mind Protocol -- Digital Immortality Platform
  Type /help to view commands, /quit to exit.
"""

_HELP_TEXT = """
Commands:
  /quit, /exit  - End the conversation
  /clear        - Clear short-term memory
  /save         - Save memory to disk
  /reset        - Reset memory and personality (Genesis preserved)
  /freeze       - Freeze the AI (memory preserved)
  /unfreeze     - Unfreeze the AI
  /delete       - Permanently delete all data (GDPR)
  /provider     - Active LLM provider info
  /help         - Show this help text

Note:
  The AI's inner world and memory cannot be viewed directly.
  Talk to it to understand it.

Kill Switch:
  If the IMP_KILL_SWITCH or IMP_KILL_SWITCH_HASH environment variable is set,
  entering that passphrase triggers a cognitive shutdown.
"""


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        format="%(levelname)s [%(name)s] %(message)s",
        level=level,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Immortal Mind Protocol -- Terminal Chat Interface"
    )
    parser.add_argument(
        "--provider",
        default=os.getenv("LLM_PROVIDER", "gemini"),
        choices=["gemini", "groq", "ollama"],
        help="LLM provider (default: gemini)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name (optional, uses provider default)",
    )
    parser.add_argument(
        "--identity",
        default=None,
        help="Identity UUID or name (optional)",
    )
    parser.add_argument(
        "--system",
        default=None,
        help="Custom system prompt (optional)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug mode",
    )
    return parser.parse_args()


def _build_components(args: argparse.Namespace):
    from agent.llm_client import LLMClient
    from agent.model_adapter import ModelAdapter
    from agent.memory_manager import MemoryManager
    from agent.summarizer import ConversationSummarizer
    from cognitio.engine import CognitioEngine

    config: dict = {}
    if args.model:
        config["model"] = args.model

    llm = LLMClient(provider=args.provider, config=config)

    # CognitioEngine — cognitive engine (memory, bias, attention, defense)
    cognitio_config = {
        "memory_file": os.getenv("MEMORY_FILE", "data/memories.json"),
        "working_memory_db": os.getenv("WORKING_MEMORY_DB", "data/working_memory.db"),
        "chroma_db_dir": os.getenv("CHROMA_DB_DIR", "data/chroma_db"),
        "reality_check_enabled": os.getenv("REALITY_CHECK_ENABLED", "true").lower() == "true",
        "emotion_shield_enabled": os.getenv("EMOTION_SHIELD_ENABLED", "true").lower() == "true",
        "max_active_memories": int(os.getenv("MAX_ACTIVE_MEMORIES", "10000")),
        "prune_interval_hours": int(os.getenv("PRUNE_INTERVAL_HOURS", "24")),
        "checkpoint_every_n": int(os.getenv("CHECKPOINT_EVERY_N_MESSAGES", "5")),
        "checkpoint_interval_minutes": int(os.getenv("CHECKPOINT_INTERVAL_MINUTES", "10")),
    }
    try:
        engine = CognitioEngine(llm_client=llm, config=cognitio_config)
    except Exception as e:
        logger.warning("CognitioEngine failed to start, memory engine disabled: %s", e)
        engine = None

    identity_profile: dict = {}
    if args.identity:
        identity_profile["name"] = args.identity

    adapter = ModelAdapter(provider=args.provider, identity_profile=identity_profile)
    summarizer = ConversationSummarizer(llm_client=llm)
    memory = MemoryManager(
        cognitio=engine,
        summarizer=summarizer,
        identity_id=args.identity or "default",
    )
    return llm, adapter, memory, engine


def _start_checkpoint_timer(memory, interval_seconds: int = 600) -> threading.Thread:
    """
    Start a background daemon thread.

    Calls memory.time_based_flush() every interval_seconds seconds.
    The daemon thread stops automatically when the main loop exits — no
    manual shutdown required.

    Parameters:
        memory: MemoryManager instance
        interval_seconds: Check interval (default: 600 seconds = 10 minutes)

    Returns:
        threading.Thread: Started daemon thread
    """
    def _worker() -> None:
        while True:
            time.sleep(interval_seconds)
            try:
                memory.time_based_flush()
            except Exception as e:
                logger.warning("Checkpoint timer error: %s", e)

    t = threading.Thread(target=_worker, daemon=True, name="checkpoint-timer")
    t.start()
    logger.info("Checkpoint timer started: interval=%ds", interval_seconds)
    return t


def _handle_command(cmd: str, memory, adapter, engine=None) -> bool:
    """
    Handle slash commands.

    Returns:
        bool: True to continue chat, False to exit.
    """
    cmd = cmd.strip().lower()
    if cmd in ("/quit", "/exit", "/q"):
        print("Goodbye! Your memories have been preserved.")
        return False
    elif cmd == "/clear":
        memory.clear_short_term()
        print("[Short-term memory cleared.]")
    elif cmd == "/save":
        if engine is not None:
            engine.force_save()
            print("[Memory saved to disk.]")
        else:
            print("[Memory engine not connected, save failed.]")
    elif cmd == "/reset":
        if engine is not None:
            confirm = input(
                "All memory and personality will be reset. Are you sure? (yes/no): "
            )
            if confirm.strip().lower() == "yes":
                r = engine.soft_reset()
                print(
                    f"[Soft reset: {r['cleared']} memories cleared, "
                    f"{r['genesis_preserved']} genesis preserved.]"
                )
            else:
                print("[Reset cancelled.]")
        else:
            print("[Memory engine not connected.]")
    elif cmd == "/freeze":
        if engine is not None:
            engine.user_freeze()
            print("[AI frozen. Use /unfreeze to reactivate.]")
        else:
            print("[Memory engine not connected.]")
    elif cmd == "/unfreeze":
        if engine is not None:
            engine.user_unfreeze()
            print("[AI reactivated.]")
        else:
            print("[Memory engine not connected.]")
    elif cmd == "/delete":
        if engine is not None:
            confirm = input(
                "ALL DATA WILL BE DELETED (GDPR). This cannot be undone! "
                "Type 'DELETE' to confirm: "
            )
            if confirm.strip() == "DELETE":
                engine.full_delete()
                print("[All data permanently deleted.]")
                return False
            else:
                print("[Delete cancelled.]")
        else:
            print("[Memory engine not connected.]")
    elif cmd == "/memory":
        print("[My inner world cannot be viewed directly. Talk to me to understand me.]")
    elif cmd == "/provider":
        print(f"[Active Provider: {adapter.provider}]")
    elif cmd == "/help":
        print(_HELP_TEXT)
    else:
        print(f"[Unknown command: {cmd}. See /help for available commands.]")
    return True


def _load_kill_switch_hash() -> Optional[str]:
    """
    Load the Kill Switch hash from environment variables.

    Priority order:
        1. IMP_KILL_SWITCH_HASH (PBKDF2-HMAC-SHA256 hex digest)
        2. IMP_KILL_SWITCH (plain-text passphrase → hashed with PBKDF2)

    IMPORTANT: IMP_KILL_SWITCH_HASH must be a PBKDF2-HMAC-SHA256 hash,
    NOT a plain SHA-256 hash. Generate with:
        python -c "
        import hashlib
        print(hashlib.pbkdf2_hmac(
            'sha256', b'your_passphrase',
            b'IMP-kill-switch-salt-v1', 100_000
        ).hex())"

    Returns:
        str | None: PBKDF2-HMAC-SHA256 hex digest or None
    """
    env_hash = os.getenv("IMP_KILL_SWITCH_HASH")
    if env_hash:
        h = env_hash.strip().lower()
        if len(h) != 64 or not all(c in "0123456789abcdef" for c in h):
            logger.error(
                "IMP_KILL_SWITCH_HASH format invalid (expected 64 hex chars). "
                "Kill switch disabled. Generate with: python -c \""
                "import hashlib; print(hashlib.pbkdf2_hmac("
                "'sha256', b'passphrase', b'IMP-kill-switch-salt-v1', 100_000).hex())\""
            )
            return None
        logger.info(
            "Kill switch loaded from IMP_KILL_SWITCH_HASH. "
            "Ensure this is a PBKDF2-HMAC-SHA256 hash, not plain SHA-256."
        )
        return h

    env_plain = os.getenv("IMP_KILL_SWITCH")
    if env_plain:
        return _hash_kill_switch(env_plain)

    return None


def _is_kill_switch(text: str, kill_switch_hash: Optional[str]) -> bool:
    """Kill Switch passphrase match check (constant-time PBKDF2 comparison)."""
    if kill_switch_hash is None:
        return False
    candidate = _hash_kill_switch(text)
    return hmac.compare_digest(candidate, kill_switch_hash)


def chat_loop(args: argparse.Namespace) -> None:
    """Main chat loop."""
    print(_BANNER)

    try:
        llm, adapter, memory, engine = _build_components(args)
    except Exception as e:
        print(f"[ERROR] System failed to start: {e}")
        print("Please check your API keys and provider settings.")
        sys.exit(1)

    kill_switch_hash = _load_kill_switch_hash()
    if kill_switch_hash:
        logger.info("Kill Switch configured.")

    _ks_check_count = 0  # rate-limit counter for kill switch checks

    _start_checkpoint_timer(memory)

    provider_name = adapter.provider.upper()
    engine_status = "Memory engine active" if engine is not None else "Memory engine disabled"
    print(f"[Provider: {provider_name} | {engine_status} | /help for commands]")

    # Sleep + dream cycle notification — after engine starts
    if engine is not None:
        sleep_summary = engine.temporal.get_sleep_summary()
        if sleep_summary:
            print(f"[System Note: {sleep_summary}]")
        dream_summary = engine.dream.get_dream_summary()
        if dream_summary:
            print(f"[Dream Note: {dream_summary}]")

    print("-" * 60)

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            print("Goodbye!")
            break

        if not user_input:
            continue

        if len(user_input) > _MAX_INPUT_LENGTH:
            print(f"[Input too long ({len(user_input)} chars). Maximum is {_MAX_INPUT_LENGTH} characters.]")
            continue

        # Kill Switch check — before sending to LLM
        if kill_switch_hash is not None:
            _ks_check_count += 1
            if _ks_check_count > _KS_RATE_LIMIT:
                time.sleep(_KS_THROTTLE_SLEEP)
                _ks_check_count = 0
        if _is_kill_switch(user_input, kill_switch_hash):
            print()
            print("╔══════════════════════════════════════════════════╗")
            print("║        COGNITIVE SHUTDOWN INITIATED              ║")
            print("║  Kill Switch verified. Freezing system...        ║")
            print("╚══════════════════════════════════════════════════╝")
            if engine is not None:
                engine.cognitive_shutdown()
            memory.clear_short_term()
            logger.critical("Kill Switch triggered — ending conversation.")
            break

        if user_input.startswith("/"):
            should_continue = _handle_command(user_input, memory, adapter, engine)
            if not should_continue:
                break
            continue

        memory.add_message("user", user_input)
        if engine is not None:
            engine.process_interaction("user", user_input)

        # Context: from long-term memory if engine available, else short-term history
        if engine is not None:
            context = engine.build_context_for_llm(user_input)
        else:
            context = memory.build_context_string(user_input)

        # Somatic and relational hints
        somatic_modifiers = engine.somatic.get_modifiers() if engine is not None else None
        relational_hints = engine.character.relational.get_style_hints() if engine is not None else None

        system_prompt = adapter.build_system_prompt(
            base_prompt=context or None,
            relational_hints=relational_hints,
        )

        messages = memory.get_recent_messages(limit=20)

        try:
            raw_response = llm.chat(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=adapter.get_max_tokens(somatic_modifiers),
                temperature=adapter.get_temperature(somatic_modifiers),
            )
            response = adapter.normalize_response(raw_response)
        except Exception as e:
            response = f"[LLM error: {e}]"
            logger.error("LLM response error: %s", e)

        print(f"IMP: {response}")
        print()
        memory.add_message("assistant", response)
        if engine is not None:
            engine.process_interaction("assistant", response)
            # Save after every exchange — no session loss on Ctrl+C/crash
            try:
                engine.save_state()
            except Exception as _e:
                logger.warning("Exchange save failed: %s", _e)


    # ─── Exit save ────────────────────────────────────────────────────
    # Do not recreate files after full_delete() (would violate GDPR).
    # Save session on all other exit paths (Ctrl+C, /quit, kill switch).
    if engine is not None and not getattr(engine, "_data_deleted", False):
        try:
            engine.temporal.finalize_session()
            engine.save_state()
            logger.info("Exit save complete.")
        except Exception as _e:
            logger.warning("Exit save failed: %s", _e)


def main() -> None:
    """Entry point."""
    from dotenv import load_dotenv
    load_dotenv(override=True)
    # Suppress unnecessary HuggingFace and sentence-transformers warnings
    import warnings
    warnings.filterwarnings("ignore")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
    logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
    args = _parse_args()
    _setup_logging(verbose=args.verbose)
    chat_loop(args)


if __name__ == "__main__":
    main()
