"""Multi-tier LiteLLM wrapper. Isolates all provider API calls."""

from __future__ import annotations

import json
import logging
from enum import Enum

from litellm import acompletion

from config import OrchestratorConfig

logger = logging.getLogger(__name__)


class ModelTier(str, Enum):
    FAST = "fast"
    STANDARD = "standard"


class LLMConfigurationError(Exception):
    """Raised when required LLM configuration is missing."""


class EmptyLLMResponseError(RuntimeError):
    """Raised when the provider returns empty or whitespace-only content."""

    def __init__(self, model: str) -> None:
        super().__init__(f"LLM '{model}' returned empty content.")
        self.model = model


class LLMClient:
    """Async LLM client that routes requests to fast or standard models."""

    def __init__(self, config: OrchestratorConfig) -> None:
        self._config = config
        self._models = {
            ModelTier.FAST: config.fast_model,
            ModelTier.STANDARD: config.standard_model,
        }

    async def complete(
        self,
        messages: list[dict[str, str]],
        tier: ModelTier = ModelTier.STANDARD,
    ) -> str:
        """Send a chat completion request and return the assistant content.

        Raises EmptyLLMResponseError if the provider returns empty or
        whitespace-only content, so callers never silently consume blanks.
        """
        params: dict = {
            "model": self._models[tier],
            "messages": messages,
            "api_key": self._config.provider_api_key,
        }
        if self._config.api_base:
            params["api_base"] = self._config.api_base

        response = await acompletion(**params)
        content = response.choices[0].message.content or ""
        if not content.strip():
            raise EmptyLLMResponseError(self._models[tier])
        return content

    async def complete_with_retry(
        self,
        messages: list[dict[str, str]],
        tier: ModelTier = ModelTier.STANDARD,
        max_attempts: int = 2,
    ) -> str:
        """Call complete() and retry on EmptyLLMResponseError.

        Retries are limited to empty-response failures.  Other exceptions
        (auth, network, rate limits) propagate immediately so they are not
        masked by retry loops.
        """
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1.")

        last_error: EmptyLLMResponseError | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                return await self.complete(messages, tier=tier)
            except EmptyLLMResponseError as err:
                last_error = err
                logger.warning(
                    "Empty response from '%s' on attempt %d/%d.",
                    err.model,
                    attempt,
                    max_attempts,
                )

        assert last_error is not None
        raise last_error

    async def complete_json(
        self,
        messages: list[dict[str, str]],
        tier: ModelTier = ModelTier.FAST,
        max_attempts: int = 2,
    ) -> list | dict:
        """Send a completion request and parse the response as JSON."""
        raw = await self.complete_with_retry(
            messages, tier=tier, max_attempts=max_attempts
        )
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        return json.loads(cleaned)
