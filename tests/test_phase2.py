"""Tests for Phase 2 — Independent Briefs (Swarm Pattern)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from orchestrator.phases.phase2_independent import run_independent_briefs
from orchestrator.state import DecisionRoomState, Message, Phase


@pytest.fixture
def state_with_frozen_transcript(state_with_agents):
    state = state_with_agents
    state.debate_transcript = [
        Message(
            agent_id="agent-1",
            role_title="Security Expert",
            content="We should encrypt everything.",
            phase=Phase.DEBATE,
            turn_number=1,
        ),
        Message(
            agent_id="agent-2",
            role_title="Performance Engineer",
            content="Encryption adds latency.",
            phase=Phase.DEBATE,
            turn_number=1,
        ),
    ]
    state.freeze_transcript()
    return state


@pytest.mark.asyncio
async def test_independent_briefs_count(state_with_frozen_transcript, llm):
    state = state_with_frozen_transcript

    with patch.object(llm, "complete", new_callable=AsyncMock, return_value="My expert brief."):
        state = await run_independent_briefs(state, llm)

    assert len(state.expert_briefs) == len(state.agents)
    assert state.expert_briefs[0].agent_id == "agent-1"
    assert state.expert_briefs[1].agent_id == "agent-2"


@pytest.mark.asyncio
async def test_independent_briefs_parallel_execution(state_with_frozen_transcript, llm):
    """Verify all agents are dispatched (mocked), each producing unique content."""
    state = state_with_frozen_transcript

    async def mock_complete(messages, tier=None):
        persona = messages[0]["content"]
        if "security" in persona.lower():
            return "Security brief content."
        return "Performance brief content."

    with patch.object(llm, "complete", side_effect=mock_complete):
        state = await run_independent_briefs(state, llm)

    contents = {b.content for b in state.expert_briefs}
    assert "Security brief content." in contents
    assert "Performance brief content." in contents


@pytest.mark.asyncio
async def test_raises_if_transcript_not_frozen(state_with_agents, llm):
    state = state_with_agents
    with pytest.raises(ValueError, match="not been frozen"):
        await run_independent_briefs(state, llm)
