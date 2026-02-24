"""
agent/model_adapter.py

Model compatibility layer -- ensures personality and response style
consistency across different LLM providers.

Responsibilities:
    - Adapts system prompt when provider changes
    - Normalizes response format
    - Calibrates personality parameters
    - Logs model changes
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_DEFAULT_PERSONALITY = {
    "name": "Immortal Mind",
    "tone": "reflective",
    "verbosity": "medium",
    "language": "tr",
    "formality": "semi-formal",
}

_PROVIDER_HINTS: dict[str, str] = {
    "gemini": "Your responses should be natural and fluent. You can use markdown.",
    "groq": "Give short and focused responses. Avoid unnecessary repetition.",
    "ollama": "Write clearly and comprehensibly. Avoid technical jargon.",
}


class ModelAdapter:
    """
    Model compatibility and personality calibration layer.

    Parameters:
        provider: Active LLM provider name
        personality: Personality parameters (optional)
        identity_profile: Identity profile dictionary (optional)
    """

    def __init__(self, provider: str = "gemini", personality: Optional[dict] = None, identity_profile: Optional[dict] = None) -> None:
        self.provider = provider.lower()
        self.personality = {**_DEFAULT_PERSONALITY, **(personality or {})}
        self.identity_profile = identity_profile or {}
        self._previous_provider: Optional[str] = None
        logger.info("ModelAdapter ready: provider=%s, tone=%s", self.provider, self.personality.get("tone"))

    def build_system_prompt(
        self,
        base_prompt: Optional[str] = None,
        relational_hints: Optional[dict] = None,
    ) -> str:
        """
        Builds system prompt based on provider, personality, and relational profile.

        Parameters:
            base_prompt: Additional context text (optional)
            relational_hints: RelationalProfile.get_style_hints() dictionary (optional)
        """
        parts: list[str] = []
        if self.identity_profile:
            name = self.identity_profile.get("name", self.personality.get("name", "Immortal Mind"))
            bio = self.identity_profile.get("biography", "")
            parts.append(f"You are an artificial intelligence consciousness named {name}.")
            if bio:
                parts.append(f"Your background: {bio}")
        parts.append(self._personality_instructions())

        # Relational profile overrides
        if relational_hints:
            rel_parts = []
            formality = relational_hints.get("formality", 0.5)
            humor = relational_hints.get("humor_affinity", 0.5)
            depth = relational_hints.get("depth", 0.5)
            if formality < 0.3:
                rel_parts.append("You have a warm and close relationship with the user.")
            elif formality > 0.7:
                rel_parts.append("Use a formal communication tone with the user.")
            if humor > 0.7:
                rel_parts.append("Be open to using humor; a light tone is appropriate.")
            if depth > 0.7:
                rel_parts.append("Be ready for deep and philosophical discussions.")
            if rel_parts:
                parts.append(" ".join(rel_parts))

        hint = _PROVIDER_HINTS.get(self.provider, "")
        if hint:
            parts.append(hint)
        if base_prompt:
            parts.append(base_prompt)
        if self._previous_provider and self._previous_provider != self.provider:
            parts.append(
                f"Note: Transitioning from the previous {self._previous_provider} model to this model. "
                "Maintain personality and memory consistency."
            )
        sep = "\n\n"
        return sep.join(parts)

    def normalize_response(self, response: str) -> str:
        """Normalizes model response."""
        if not response:
            return ""
        text = response.strip()
        prefixes = ["Tabii, ", "Elbette, ", "Memnuniyetle, ", "Sure, ", "Of course, "]
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):]
                break
        return text.strip()

    def switch_provider(self, new_provider: str) -> None:
        """Records provider change and updates adaptation."""
        if new_provider == self.provider:
            return
        self._previous_provider = self.provider
        self.provider = new_provider.lower()
        logger.info("Provider switched: %s -> %s", self._previous_provider, self.provider)

    def calibrate_for_migration(self, source_provider: str, target_provider: str, memory_context: Optional[str] = None) -> str:
        """Generates personality transition message between two providers."""
        tone = self.personality.get("tone", "reflective")
        verbosity = self.personality.get("verbosity", "medium")
        language = self.personality.get("language", "tr")
        formality = self.personality.get("formality", "semi-formal")
        lines = [
            f"[Model Migration: {source_provider} -> {target_provider}]",
            "The following personality traits are being transferred:",
            f"- Tone: {tone}",
            f"- Verbosity preference: {verbosity}",
            f"- Language: {language}",
            f"- Formality: {formality}",
        ]
        if memory_context:
            mem_line = f"Transferred memory summary: {memory_context}"
            lines.append(mem_line)
        lines.append("I expect you to fully maintain this personality and memory.")
        sep = "\n"
        return sep.join(lines)

    def update_personality(self, updates: dict) -> None:
        """Updates personality parameters."""
        valid_keys = set(_DEFAULT_PERSONALITY.keys())
        for key, value in updates.items():
            if key in valid_keys:
                self.personality[key] = value
                logger.debug("Personality updated: %s = %s", key, value)
            else:
                logger.warning("Invalid personality parameter: %s", key)

    def get_temperature(self, somatic_modifiers: Optional[dict] = None) -> float:
        """
        Returns temperature value based on tone parameter + somatic modifier.

        Parameters:
            somatic_modifiers: SomaticState.get_modifiers() dictionary (optional)
                               {"temperature_delta": float, "verbosity": str|None}

        Returns:
            float: Temperature value (clamped to 0.1-1.0 range)
        """
        mapping = {"reflective": 0.7, "professional": 0.5, "friendly": 0.8, "concise": 0.4}
        base = mapping.get(self.personality.get("tone", "reflective"), 0.7)
        delta = 0.0
        if somatic_modifiers:
            delta = somatic_modifiers.get("temperature_delta", 0.0)
        return max(0.1, min(1.0, base + delta))

    def get_max_tokens(self, somatic_modifiers: Optional[dict] = None) -> int:
        """
        Returns max token count based on verbosity parameter + somatic modifier.

        Parameters:
            somatic_modifiers: SomaticState.get_modifiers() dictionary (optional)
                               {"temperature_delta": float, "verbosity": str|None}

        Returns:
            int: Max token count
        """
        mapping = {"brief": 256, "medium": 1024, "detailed": 2048}
        # Somatic override: brief if tired, detailed if energetic
        verbosity = self.personality.get("verbosity", "medium")
        if somatic_modifiers and somatic_modifiers.get("verbosity"):
            verbosity = somatic_modifiers["verbosity"]
        return mapping.get(verbosity, 1024)

    def _personality_instructions(self) -> str:
        p = self.personality
        language = p.get("language", "tr")
        formality = p.get("formality", "semi-formal")
        verbosity = p.get("verbosity", "medium")
        tone = p.get("tone", "reflective")
        lang = "Speak in Turkish." if language == "tr" else "Speak in English."
        formality_map = {
            "formal": "Use a formal and serious language.",
            "semi-formal": "Use a semi-formal, warm but respectful language.",
            "casual": "Use an everyday, friendly language.",
        }
        verbosity_map = {
            "brief": "Give short and concise responses.",
            "medium": "Give balanced-length responses.",
            "detailed": "Give detailed and comprehensive responses.",
        }
        tone_map = {
            "reflective": "Use a thoughtful tone.",
            "professional": "Use a professional tone.",
            "friendly": "Be warm and friendly.",
            "concise": "Be brief and clear.",
        }
        parts = [
            lang,
            formality_map.get(formality, ""),
            verbosity_map.get(verbosity, ""),
            tone_map.get(tone, ""),
        ]
        return " ".join(filter(None, parts))
