"""Centralized configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


class LLMConfigurationError(Exception):
    """Raised when required LLM configuration is missing."""


@dataclass(frozen=True)
class OrchestratorConfig:
    """Immutable configuration for the Decision Room pipeline."""

    provider_api_key: str
    fast_model: str
    standard_model: str
    api_base: str | None = None
    max_debate_turns: int = 3
    min_agents: int = 2
    max_agents: int = 4

    @classmethod
    def from_env(cls) -> OrchestratorConfig:
        """
        Create an OrchestratorConfig populated from environment variables.
        
        Reads the following environment variables (and uses defaults when not set): PROVIDER_API_KEY (required), LLM_MODEL_FAST (default "openai/gpt-4o-mini"), LLM_MODEL_STANDARD (default "openai/gpt-4o"), LLM_API_BASE (empty string is treated as None), and MAX_DEBATE_TURNS (default "3", converted to int). Constructs and returns an OrchestratorConfig using these values.
        
        Returns:
            OrchestratorConfig: Configuration instance built from the environment.
        
        Raises:
            LLMConfigurationError: If PROVIDER_API_KEY is missing or empty.
        """
        api_key = os.getenv("PROVIDER_API_KEY", "")
        if not api_key:
            raise LLMConfigurationError(
                "Missing PROVIDER_API_KEY in .env. Add it and try again."
            )

        fast_model = os.getenv("LLM_MODEL_FAST", "openai/gpt-4o-mini")
        standard_model = os.getenv("LLM_MODEL_STANDARD", "openai/gpt-4o")
        api_base = os.getenv("LLM_API_BASE") or None
        max_turns = int(os.getenv("MAX_DEBATE_TURNS", "3"))

        return cls(
            provider_api_key=api_key,
            fast_model=fast_model,
            standard_model=standard_model,
            api_base=api_base,
            max_debate_turns=max_turns,
        )
