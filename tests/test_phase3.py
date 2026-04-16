"""Tests for Phase 3 — Aggregator (Master Agent)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from agents.models import ExpertBrief
from orchestrator.phases.phase3_aggregator import run_aggregation
from orchestrator.state import Phase


@pytest.fixture
def state_with_briefs(state_with_agents):
    state = state_with_agents
    state.expert_briefs = [
        ExpertBrief(agent_id="agent-1", role_title="Security Expert", content="Use TLS everywhere."),
        ExpertBrief(agent_id="agent-2", role_title="Performance Engineer", content="Cache aggressively."),
    ]
    return state


@pytest.mark.asyncio
async def test_aggregation_produces_final_decision(state_with_briefs, llm):
    with patch.object(llm, "complete", new_callable=AsyncMock, return_value="Final synthesized decision."):
        state = await run_aggregation(state_with_briefs, llm)

    assert state.final_decision == "Final synthesized decision."
    assert state.current_phase == Phase.AGGREGATION


@pytest.mark.asyncio
async def test_aggregation_receives_all_briefs(state_with_briefs, llm):
    captured_messages: list = []

    async def capture(messages, tier=None):
        captured_messages.extend(messages)
        return "Done."

    with patch.object(llm, "complete", side_effect=capture):
        await run_aggregation(state_with_briefs, llm)

    user_msg = captured_messages[1]["content"]
    assert "Security Expert" in user_msg
    assert "Performance Engineer" in user_msg
    assert "Use TLS everywhere." in user_msg
    assert "Cache aggressively." in user_msg
