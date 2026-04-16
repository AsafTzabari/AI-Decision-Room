"""Tests for Phase 0 — Recruiter."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from agents.cognitive_framework import COGNITIVE_FRAMEWORK_RULES
from orchestrator.phases.phase0_recruiter import recruit_agents
from orchestrator.state import DecisionRoomState


@pytest.mark.asyncio
async def test_recruit_agents_creates_correct_count(config, llm):
    recruiter_response = [
        {"role_title": "Security Expert", "base_persona": "You are a security expert."},
        {"role_title": "Backend Architect", "base_persona": "You are a backend architect."},
        {"role_title": "DevOps Lead", "base_persona": "You are a DevOps lead."},
    ]

    with patch.object(llm, "complete_json", new_callable=AsyncMock, return_value=recruiter_response):
        state = DecisionRoomState(user_prompt="Should we migrate to Kubernetes?")
        state = await recruit_agents(state, llm, config)

    assert len(state.agents) == 3
    assert state.agents[0].role_title == "Security Expert"
    assert state.agents[1].role_title == "Backend Architect"
    assert state.agents[2].role_title == "DevOps Lead"


@pytest.mark.asyncio
async def test_cognitive_framework_injected(config, llm):
    recruiter_response = [
        {"role_title": "Expert A", "base_persona": "You are expert A."},
        {"role_title": "Expert B", "base_persona": "You are expert B."},
    ]

    with patch.object(llm, "complete_json", new_callable=AsyncMock, return_value=recruiter_response):
        state = DecisionRoomState(user_prompt="test")
        state = await recruit_agents(state, llm, config)

    for agent in state.agents:
        assert COGNITIVE_FRAMEWORK_RULES in agent.system_prompt
        assert agent.base_persona in agent.system_prompt


@pytest.mark.asyncio
async def test_recruiter_rejects_wrong_count(config, llm):
    too_many = [
        {"role_title": f"Expert {i}", "base_persona": f"Persona {i}"}
        for i in range(6)
    ]

    with patch.object(llm, "complete_json", new_callable=AsyncMock, return_value=too_many):
        state = DecisionRoomState(user_prompt="test")
        with pytest.raises(ValueError, match="agents"):
            await recruit_agents(state, llm, config)
