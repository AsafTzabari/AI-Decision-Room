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


@pytest.mark.asyncio
async def test_chatroom_uses_only_system_and_user_roles(state_with_agents, llm):
    """Provider compatibility: never replay history as synthetic assistant turns."""
    state = state_with_agents
    state.max_debate_turns = 2
    captured_calls: list[list[dict[str, str]]] = []

    async def capture(messages, tier=None):
        captured_calls.append(messages)
        return "Reply."

    with patch.object(llm, "complete", side_effect=capture):
        await run_chatroom(state, llm)

    for call_messages in captured_calls:
        roles = [m["role"] for m in call_messages]
        assert roles == ["system", "user"], f"Unexpected roles: {roles}"


@pytest.mark.asyncio
async def test_chatroom_includes_transcript_in_user_message(state_with_agents, llm):
    """Later speakers must see prior debate content inside their user message."""
    state = state_with_agents
    state.max_debate_turns = 2
    call_index = {"i": 0}
    captured_user_messages: list[str] = []

    async def capture(messages, tier=None):
        captured_user_messages.append(messages[1]["content"])
        call_index["i"] += 1
        return f"Reply number {call_index['i']}"

    with patch.object(llm, "complete", side_effect=capture):
        await run_chatroom(state, llm)

    first_user_msg = captured_user_messages[0]
    assert "no messages yet" in first_user_msg.lower() or "no prior" in first_user_msg.lower()
    assert "speaking first" in first_user_msg.lower()

    second_user_msg = captured_user_messages[1]
    assert "Reply number 1" in second_user_msg
    assert "Security Expert" in second_user_msg


@pytest.mark.asyncio
async def test_chatroom_propagates_empty_response_error(state_with_agents, llm):
    """If retries are exhausted on empty content, the phase must surface the error."""
    from llm.client import EmptyLLMResponseError

    state = state_with_agents
    state.max_debate_turns = 1

    async def always_empty(**kwargs):
        class Choice:
            class Msg:
                content = "   "
            message = Msg()

        class Resp:
            choices = [Choice()]

        return Resp()

    with patch("llm.client.acompletion", side_effect=always_empty):
        with pytest.raises(EmptyLLMResponseError):
            await run_chatroom(state, llm)
