"""Tests for Phase 1 — Chat Room (sequential debate loop)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from orchestrator.phases.phase1_chatroom import run_chatroom
from orchestrator.state import Phase


@pytest.mark.asyncio
async def test_chatroom_produces_correct_message_count(state_with_agents, llm):
    state = state_with_agents
    state.max_debate_turns = 3
    num_agents = len(state.agents)

    with patch.object(llm, "complete", new_callable=AsyncMock, return_value="Mock debate reply."):
        state = await run_chatroom(state, llm)

    expected = num_agents * 3
    assert len(state.debate_transcript) == expected
    assert state.debate_turn_count == 3
    assert state.current_phase == Phase.DEBATE


@pytest.mark.asyncio
async def test_chatroom_sequential_ordering(state_with_agents, llm):
    state = state_with_agents
    state.max_debate_turns = 2
    call_order: list[str] = []

    async def mock_complete(messages, tier=None):
        agent_id = "agent-1" if "security" in messages[0]["content"].lower() else "agent-2"
        call_order.append(agent_id)
        return f"Reply from {agent_id}"

    with patch.object(llm, "complete", side_effect=mock_complete):
        state = await run_chatroom(state, llm)

    assert state.debate_transcript[0].role_title == "Security Expert"
    assert state.debate_transcript[1].role_title == "Performance Engineer"
    assert state.debate_transcript[0].turn_number == 1
    assert state.debate_transcript[2].turn_number == 2
