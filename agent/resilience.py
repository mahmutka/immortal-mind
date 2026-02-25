"""
agent/resilience.py

Fallback Chain Manager.
"""

import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

_DEFAULT_RETRY_AFTER = 300
_DEFAULT_MAX_RETRIES = 3


class ProviderState:
    """Current state of a provider."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.enabled: bool = True
        self.consecutive_failures: int = 0
        self.last_failure_time: float = 0.0
        self.total_requests: int = 0
        self.total_failures: int = 0




class FallbackChain:
    """Single fallback chain manager."""

    def __init__(self, providers, factory, retry_after=_DEFAULT_RETRY_AFTER, max_retries=_DEFAULT_MAX_RETRIES):
        self.factory = factory
        self.retry_after = retry_after
        self.max_retries = max_retries
        self._states = {p: ProviderState(name=p) for p in providers}
        self._instances: dict = {}
        self._order = list(providers)

    def execute(self, action):
        """Tries providers in the fallback chain until a successful result is returned."""
        errors = []
        for provider_name in self._active_providers():
            instance = self._get_instance(provider_name)
            if instance is None:
                errors.append(f"{provider_name}: could not be initialized")
                self._record_failure(provider_name)
                continue
            state = self._states[provider_name]
            state.total_requests += 1
            try:
                result = action(instance)
                logger.debug("Provider succeeded: %s", provider_name)
                state.consecutive_failures = 0
                return result
            except Exception as e:
                errors.append(f"{provider_name}: {e}")
                logger.warning("Provider error (%s): %s", provider_name, e)
                self._record_failure(provider_name)
        sep = "; "
        raise RuntimeError(f"All providers failed: {sep.join(errors)}")

    def get_primary(self):
        """Returns the first active provider."""
        for name in self._active_providers():
            inst = self._get_instance(name)
            if inst is not None:
                return inst
        return None

    def get_primary_name(self):
        """Returns the name of the active primary provider."""
        for name in self._active_providers():
            return name
        return None

    def health_check_all(self):
        """Checks the health status of all providers."""
        results = {}
        for name in self._order:
            inst = self._get_instance(name)
            if inst is None:
                results[name] = False
                continue
            try:
                checker = getattr(inst, "health_check", None)
                results[name] = bool(checker()) if checker else True
            except Exception:
                results[name] = False
                self._record_failure(name)
        return results

    def reset_provider(self, provider_name: str) -> None:
        """Re-enables a disabled provider."""
        if provider_name in self._states:
            state = self._states[provider_name]
            state.enabled = True
            state.consecutive_failures = 0
            logger.info("Provider reset: %s", provider_name)

    def get_stats(self):
        """Returns statistics for all providers."""
        return {
            name: {
                "enabled": s.enabled,
                "consecutive_failures": s.consecutive_failures,
                "total_requests": s.total_requests,
                "total_failures": s.total_failures,
                "failure_rate": s.total_failures / max(s.total_requests, 1),
            }
            for name, s in self._states.items()
        }

    def _active_providers(self):
        now = time.monotonic()
        active = []
        for name in self._order:
            state = self._states[name]
            if not state.enabled:
                if now - state.last_failure_time >= self.retry_after:
                    state.enabled = True
                    state.consecutive_failures = 0
                    logger.info("Provider re-enabled: %s", name)
                else:
                    continue
            active.append(name)
        return active

    def _get_instance(self, provider_name):
        if provider_name not in self._instances:
            try:
                self._instances[provider_name] = self.factory(provider_name)
            except Exception as e:
                logger.error("Provider instance could not be created (%s): %s", provider_name, e)
                return None
        return self._instances[provider_name]

    def _record_failure(self, provider_name):
        state = self._states[provider_name]
        state.consecutive_failures += 1
        state.total_failures += 1
        state.last_failure_time = time.monotonic()
        if state.consecutive_failures >= self.max_retries:
            state.enabled = False
            logger.warning("Provider disabled: %s", provider_name)


class ResilienceManager:
    """Class that centrally manages all fallback chains."""

    LLM_ORDER = ["gemini", "groq", "ollama"]
    BLOCKCHAIN_ORDER = ["alchemy", "infura", "local"]
    STORAGE_ORDER = ["ipfs", "arweave", "local"]

    def __init__(self, llm_factory=None, blockchain_factory=None, storage_factory=None, config=None):
        self.config = config or {}
        retry_after = self.config.get("retry_after", _DEFAULT_RETRY_AFTER)
        max_retries = self.config.get("max_retries", _DEFAULT_MAX_RETRIES)
        self.llm = None
        self.blockchain = None
        self.storage = None
        if llm_factory:
            self.llm = FallbackChain(self.config.get("llm_order", self.LLM_ORDER), llm_factory, retry_after, max_retries)
            logger.info("LLM fallback chain established: %s", self.LLM_ORDER)
        if blockchain_factory:
            self.blockchain = FallbackChain(self.config.get("blockchain_order", self.BLOCKCHAIN_ORDER), blockchain_factory, retry_after, max_retries)
            logger.info("Blockchain fallback chain established.")
        if storage_factory:
            self.storage = FallbackChain(self.config.get("storage_order", self.STORAGE_ORDER), storage_factory, retry_after, max_retries)
            logger.info("Storage fallback chain established.")

    def llm_complete(self, prompt: str, **kwargs) -> str:
        """Completes text using the LLM fallback chain."""
        if self.llm is None:
            raise RuntimeError("LLM chain is not defined.")
        return self.llm.execute(lambda client: client.complete(prompt, **kwargs))

    def llm_chat(self, messages: list[dict], **kwargs) -> str:
        """Completes chat using the LLM fallback chain."""
        if self.llm is None:
            raise RuntimeError("LLM chain is not defined.")
        return self.llm.execute(lambda client: client.chat(messages, **kwargs))

    def get_active_llm(self):
        """Returns the active LLM client."""
        return self.llm.get_primary() if self.llm else None

    def get_active_llm_name(self):
        """Returns the active LLM provider name."""
        return self.llm.get_primary_name() if self.llm else None

    def health_report(self) -> dict:
        """Health report for all chains."""
        report: dict = {}
        if self.llm:
            report["llm"] = self.llm.health_check_all()
        if self.blockchain:
            report["blockchain"] = self.blockchain.health_check_all()
        if self.storage:
            report["storage"] = self.storage.health_check_all()
        return report

    def get_full_stats(self) -> dict:
        """Statistics for all chains."""
        stats: dict = {}
        if self.llm:
            stats["llm"] = self.llm.get_stats()
        if self.blockchain:
            stats["blockchain"] = self.blockchain.get_stats()
        if self.storage:
            stats["storage"] = self.storage.get_stats()
        return stats
