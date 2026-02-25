"""
agent/llm_client.py

LLM API wrapper — Gemini, Groq, and Ollama support.
"""

import json
import logging
import os
import re
import time
from typing import Optional

logger = logging.getLogger(__name__)


class LLMClient:
    """
    LLM API client.

    Supported providers:
        - gemini: Google Gemini API
        - groq: Groq API
        - ollama: Local Ollama

    Parameters:
        provider: LLM provider name
        config: Provider-specific configuration
    """

    SUPPORTED_PROVIDERS = ("gemini", "groq", "ollama")
    _MAX_RETRIES = 3
    _RETRY_BASE_DELAY = 1.0  # seconds — doubles each attempt (1s, 2s, 4s)

    def __init__(self, provider: str = "gemini", config: Optional[dict] = None) -> None:
        self.provider = provider.lower()
        self.config = config or {}
        self._client = None
        if self.provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}.")
        self._initialize()

    def _initialize(self) -> None:
        try:
            if self.provider == "gemini":
                self._init_gemini()
            elif self.provider == "groq":
                self._init_groq()
            elif self.provider == "ollama":
                self._init_ollama()
            logger.info("LLMClient initialized: provider=%s", self.provider)
        except Exception as e:
            logger.error("LLMClient could not be initialized (%s): %s", self.provider, e)
            raise

    def _init_gemini(self) -> None:
        from google import genai
        api_key = self.config.get("api_key") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found")
        self._client = genai.Client(api_key=api_key)
        self._gemini_model = self.config.get("model") or os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")
        logger.debug("Gemini client ready: model=%s", self._gemini_model)

    def _init_groq(self) -> None:
        from groq import Groq
        api_key = self.config.get("api_key") or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found")
        self._client = Groq(api_key=api_key)
        self._groq_model = self.config.get("model", "llama-3.1-8b-instant")
        logger.debug("Groq client ready: model=%s", self._groq_model)

    def _init_ollama(self) -> None:
        import requests as req
        base_url = self.config.get("base_url") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self._ollama_url = f"{base_url}/api/chat"
        self._ollama_model = self.config.get("model") or os.getenv("OLLAMA_MODEL", "llama3.2")
        self._session = req.Session()
        logger.debug("Ollama client ready: url=%s, model=%s", self._ollama_url, self._ollama_model)

    def complete(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 1024, temperature: float = 0.7) -> str:
        """Single-shot text completion with exponential backoff retry."""
        last_exc: Optional[Exception] = None
        for attempt in range(self._MAX_RETRIES):
            try:
                if self.provider == "gemini":
                    return self._complete_gemini(prompt, system_prompt, max_tokens, temperature)
                elif self.provider == "groq":
                    return self._complete_groq(prompt, system_prompt, max_tokens, temperature)
                elif self.provider == "ollama":
                    return self._complete_ollama(prompt, system_prompt, max_tokens, temperature)
            except Exception as e:
                last_exc = e
                delay = self._RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning("LLM complete error (%s), attempt %d/%d, retrying in %.1fs: %s",
                               self.provider, attempt + 1, self._MAX_RETRIES, delay, e)
                time.sleep(delay)
        logger.error("LLM complete failed after %d attempts (%s): %s", self._MAX_RETRIES, self.provider, last_exc)
        raise last_exc

    def chat(self, messages: list[dict], system_prompt: Optional[str] = None, max_tokens: int = 1024, temperature: float = 0.7) -> str:
        """Multi-turn chat completion with exponential backoff retry."""
        last_exc: Optional[Exception] = None
        for attempt in range(self._MAX_RETRIES):
            try:
                if self.provider == "gemini":
                    return self._chat_gemini(messages, system_prompt, max_tokens, temperature)
                elif self.provider == "groq":
                    return self._chat_groq(messages, system_prompt, max_tokens, temperature)
                elif self.provider == "ollama":
                    return self._chat_ollama(messages, system_prompt, max_tokens, temperature)
            except Exception as e:
                last_exc = e
                delay = self._RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning("LLM chat error (%s), attempt %d/%d, retrying in %.1fs: %s",
                               self.provider, attempt + 1, self._MAX_RETRIES, delay, e)
                time.sleep(delay)
        logger.error("LLM chat failed after %d attempts (%s): %s", self._MAX_RETRIES, self.provider, last_exc)
        raise last_exc

    def health_check(self) -> bool:
        """Check whether the provider is accessible."""
        try:
            return bool(self.complete("ping", max_tokens=5))
        except Exception:
            return False

    def complete_json(
        self,
        prompt: str,
        expected_keys: Optional[list[str]] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.2,
    ) -> dict:
        """
        LLM request expecting JSON output. Attempts repair even if small
        models (Ollama) produce malformed JSON.

        Parameters:
            prompt: User request
            expected_keys: Expected JSON fields — missing ones are filled with None
            system_prompt: System prompt (optional)
            max_tokens: Maximum token count
            temperature: Recommended to keep low (0.2) — deterministic output

        Returns:
            dict: Parsed JSON. If repair also fails, returns {key: None} for expected_keys.
        """
        json_instruction = (
            "\n\nREPLY ONLY IN VALID JSON FORMAT. "
            "Do NOT add explanations, markdown, or code blocks."
        )
        full_prompt = prompt + json_instruction
        try:
            raw = self.complete(
                full_prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return self._parse_json_safe(raw, expected_keys)
        except Exception as e:
            logger.warning("complete_json LLM error: %s", e)
            return {k: None for k in (expected_keys or [])}

    @staticmethod
    def _parse_json_safe(text: str, expected_keys: Optional[list[str]] = None) -> dict:
        """
        Extracts and repairs JSON from LLM output.

        Attempt order:
            1. Direct json.loads()
            2. From inside a markdown code block (```json ... ```)
            3. First { ... } block

        Parameters:
            text: Raw LLM output
            expected_keys: Expected fields — missing ones are added as None

        Returns:
            dict: Parsed data or {key: None} fallback
        """
        def _fill_defaults(data: dict) -> dict:
            if expected_keys:
                for key in expected_keys:
                    data.setdefault(key, None)
            return data

        # 1. Direct parse
        try:
            data = json.loads(text.strip())
            if isinstance(data, dict):
                return _fill_defaults(data)
        except json.JSONDecodeError:
            pass

        # 2. Markdown code block
        match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
        if match:
            try:
                data = json.loads(match.group(1))
                if isinstance(data, dict):
                    return _fill_defaults(data)
            except json.JSONDecodeError:
                pass

        # 3. First { ... } block — regex-free JSON scan (no ReDoS risk)
        if len(text) <= 8192:
            idx = text.find("{")
            if idx != -1:
                try:
                    data, _ = json.JSONDecoder().raw_decode(text, idx)
                    if isinstance(data, dict):
                        return _fill_defaults(data)
                except json.JSONDecodeError:
                    pass

        logger.warning("JSON parse failed. Raw output (first 120 chars): %s", text[:120])
        return {k: None for k in (expected_keys or [])}

    def _complete_gemini(self, prompt, system_prompt, max_tokens, temperature) -> str:
        from google.genai import types
        config = types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
            system_instruction=system_prompt or None,
        )
        resp = self._client.models.generate_content(
            model=self._gemini_model,
            contents=prompt,
            config=config,
        )
        return resp.text

    def _chat_gemini(self, messages, system_prompt, max_tokens, temperature) -> str:
        from google.genai import types
        history = []
        for msg in messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            history.append(
                types.Content(role=role, parts=[types.Part(text=msg["content"])])
            )
        config = types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
            system_instruction=system_prompt or None,
        )
        chat = self._client.chats.create(
            model=self._gemini_model,
            config=config,
            history=history,
        )
        resp = chat.send_message(messages[-1]["content"])
        return resp.text

    def _complete_groq(self, prompt, system_prompt, max_tokens, temperature) -> str:
        msgs: list[dict] = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.append({"role": "user", "content": prompt})
        resp = self._client.chat.completions.create(model=self._groq_model, messages=msgs, max_tokens=max_tokens, temperature=temperature)
        return resp.choices[0].message.content

    def _chat_groq(self, messages, system_prompt, max_tokens, temperature) -> str:
        msgs: list[dict] = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)
        resp = self._client.chat.completions.create(model=self._groq_model, messages=msgs, max_tokens=max_tokens, temperature=temperature)
        return resp.choices[0].message.content

    def _complete_ollama(self, prompt, system_prompt, max_tokens, temperature) -> str:
        msgs: list[dict] = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.append({"role": "user", "content": prompt})
        return self._ollama_request(msgs, max_tokens, temperature)

    def _chat_ollama(self, messages, system_prompt, max_tokens, temperature) -> str:
        msgs: list[dict] = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)
        return self._ollama_request(msgs, max_tokens, temperature)

    def _ollama_request(self, messages, max_tokens, temperature) -> str:
        payload = {"model": self._ollama_model, "messages": messages, "stream": False, "options": {"num_predict": max_tokens, "temperature": temperature}}
        resp = self._session.post(self._ollama_url, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()["message"]["content"]
