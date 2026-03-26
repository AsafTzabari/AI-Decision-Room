"""LLM client wrapper for provider-agnostic chat completions via LiteLLM."""

from __future__ import annotations

import os
from typing import List, Dict

from dotenv import load_dotenv
from litellm import completion


class LLMConfigurationError(Exception):
    """Raised when required LLM configuration is missing."""


def _load_config() -> tuple[str, str, str | None]:
    """Load and validate required environment configuration."""
    load_dotenv()

    api_key = os.getenv("PROVIDER_API_KEY")
    model = os.getenv("LLM_MODEL")
    api_base = os.getenv("LLM_API_BASE")

    if not api_key:
        raise LLMConfigurationError(
            "Missing PROVIDER_API_KEY in .env. Add it and try again."
        )
    if not model:
        raise LLMConfigurationError("Missing LLM_MODEL in .env. Add it and try again.")

    return api_key, model, api_base


def generate_reply(messages: List[Dict[str, str]]) -> str:
    """Generate an assistant reply from conversation messages."""
    api_key, model, api_base = _load_config()

    params = {
        "model": model,
        "messages": messages,
        "api_key": api_key,
    }
    if api_base:
        params["api_base"] = api_base

    response = completion(**params)
    return response.choices[0].message.content or ""
