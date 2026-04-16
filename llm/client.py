"""Multi-tier LiteLLM wrapper. Isolates all provider API calls."""

from __future__ import annotations

import json
from enum import Enum

from litellm import acompletion

from config import OrchestratorConfig


class ModelTier(str, Enum):
    FAST = "fast"
    STANDARD = "standard"


class LLMConfigurationError(Exception):
    """Raised when required LLM configuration is missing."""


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
        """Send a chat completion request and return the assistant content."""
        params: dict = {
            "model": self._models[tier],
            "messages": messages,
            "api_key": self._config.provider_api_key,
        }
        if self._config.api_base:
            params["api_base"] = self._config.api_base

        response = await acompletion(**params)
        return response.choices[0].message.content or ""

    async def complete_json(
        self,
        messages: list[dict[str, str]],
        tier: ModelTier = ModelTier.FAST,
    ) -> list | dict:
        """Send a completion request and parse the response as JSON."""
        raw = await self.complete(messages, tier=tier)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        return json.loads(cleaned)
