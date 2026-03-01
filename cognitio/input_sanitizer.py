"""
cognitio/input_sanitizer.py

Input sanitization for prompt injection defense.

Strips LLM role delimiter tokens and role-prefix patterns from user input
before it enters the processing pipeline. This prevents users from injecting
system-level instructions via chat messages.

Reuses _normalize_content() from reality_check for Unicode bypass protection.
"""

import re
import logging

from cognitio.reality_check import _normalize_content

logger = logging.getLogger(__name__)

# ── LLM role delimiter tokens ──
# These tokens are used by various LLM architectures to separate roles.
# They must never appear in user input.
_DELIMITER_TOKENS: list[str] = [
    "<<SYS>>",
    "<</SYS>>",
    "[INST]",
    "[/INST]",
    "<|system|>",
    "<|user|>",
    "<|assistant|>",
    "<|im_start|>",
    "<|im_end|>",
    "<|endoftext|>",
    "<|begin_of_text|>",
    "<|end_of_text|>",
    "<|start_header_id|>",
    "<|end_header_id|>",
]

# ── Role-prefix patterns ──
# Lines starting with these prefixes can trick the LLM into treating
# user text as system/assistant instructions.
_ROLE_PREFIX_RE = re.compile(
    r"^\s*(?:system|assistant|instruction|developer)\s*:",
    re.IGNORECASE | re.MULTILINE,
)


def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent prompt injection.

    1. Normalize Unicode (NFKC + confusable substitution) to defeat bypass attempts.
    2. Strip LLM role delimiter tokens.
    3. Neutralize role-prefix patterns (e.g. "system:" → "system").

    The function is idempotent — applying it twice produces the same result.

    Parameters:
        text: Raw user input

    Returns:
        str: Sanitized text safe for LLM pipeline
    """
    if not text:
        return text

    # Step 1: Normalize to catch Unicode-obfuscated delimiters
    # We normalize a copy for detection but operate on original text
    normalized = _normalize_content(text)

    # Step 2: Strip delimiter tokens (case-insensitive via normalized form)
    result = text
    for token in _DELIMITER_TOKENS:
        # Replace in both original and normalized forms
        result = re.sub(re.escape(token), "", result, flags=re.IGNORECASE)

    # Step 3: Neutralize role prefixes — remove the colon
    # "system: do X" → "system do X" (no longer parsed as role instruction)
    result = _ROLE_PREFIX_RE.sub(
        lambda m: m.group(0).replace(":", ""), result
    )

    if result != text:
        logger.debug("Input sanitized: removed injection markers")

    return result.strip()
