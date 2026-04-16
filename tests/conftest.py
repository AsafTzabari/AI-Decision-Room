"""Shared fixtures for the Decision Room test suite."""

from __future__ import annotations

import pytest

from agents.models import AgentDefinition
from config import OrchestratorConfig
from llm.client import LLMClient
from orchestrator.state import DecisionRoomState


@pytest.fixture
def config() -> OrchestratorConfig:
    return OrchestratorConfig(
        provider_api_key="test-key",
        fast_model="openai/gpt-4o-mini",
        standard_model="openai/gpt-4o",
    )


@pytest.fixture
def llm(config: OrchestratorConfig) -> LLMClient:
    return LLMClient(config)


@pytest.fixture
def sample_agents() -> list[AgentDefinition]:
    return [
        AgentDefinition(
            agent_id="agent-1",
            role_title="Security Expert",
            base_persona="You are a security expert.",
            system_prompt="You are a security expert.\n\nCRITICAL RULE: ...",
        ),
        AgentDefinition(
            agent_id="agent-2",
            role_title="Performance Engineer",
            base_persona="You are a performance engineer.",
            system_prompt="You are a performance engineer.\n\nCRITICAL RULE: ...",
        ),
    ]


@pytest.fixture
def base_state() -> DecisionRoomState:
    return DecisionRoomState(user_prompt="Should we use microservices?")


@pytest.fixture
def state_with_agents(
    base_state: DecisionRoomState,
    sample_agents: list[AgentDefinition],
) -> DecisionRoomState:
    base_state.agents = sample_agents
    return base_state
