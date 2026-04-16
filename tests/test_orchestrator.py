"""Tests for the SystemOrchestrator end-to-end pipeline."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from config import OrchestratorConfig
from orchestrator.engine import SystemOrchestrator
from orchestrator.state import Phase


@pytest.fixture
def orch_config() -> OrchestratorConfig:
    return OrchestratorConfig(
        provider_api_key="test-key",
        fast_model="openai/gpt-4o-mini",
        standard_model="openai/gpt-4o",
        max_debate_turns=2,
    )


@pytest.mark.asyncio
async def test_full_pipeline(orch_config):
    orchestrator = SystemOrchestrator(config=orch_config)

    recruiter_json = json.dumps([
        {"role_title": "Expert A", "base_persona": "You are expert A."},
        {"role_title": "Expert B", "base_persona": "You are expert B."},
    ])

    call_count = 0

    async def mock_acompletion(**kwargs):
        nonlocal call_count
        call_count += 1

        class Choice:
            class Msg:
                content = None
            message = Msg()

        class Resp:
            choices = [Choice()]

        messages = kwargs.get("messages", [])
        system = messages[0]["content"] if messages else ""

        if "Recruiter" in system:
            Resp.choices[0].message.content = recruiter_json
        elif call_count <= 5:
            Resp.choices[0].message.content = f"Debate reply {call_count}"
        elif call_count <= 7:
            Resp.choices[0].message.content = f"Expert brief {call_count}"
        else:
            Resp.choices[0].message.content = "Final aggregated decision."

        return Resp()

    with patch("llm.client.acompletion", side_effect=mock_acompletion):
        state = await orchestrator.run("Should we use microservices?")

    assert state.current_phase == Phase.COMPLETE
    assert len(state.agents) == 2
    assert state.debate_turn_count == 2
    assert len(state.debate_transcript) == 4  # 2 agents * 2 turns
    assert state.frozen_transcript is not None
    assert len(state.expert_briefs) == 2
    assert state.final_decision == "Final aggregated decision."
