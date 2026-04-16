"""Phase 1 — The Chat Room (Loop Pattern).

Agents debate sequentially over 3-4 rounds.  Each agent sees the full
chat history so far and must critique the previous message before adding
its own analysis (enforced by the Cognitive Framework in its system prompt).
"""

from __future__ import annotations

from llm.client import LLMClient, ModelTier
from orchestrator.state import DecisionRoomState, Message, Phase


async def run_chatroom(
    state: DecisionRoomState,
    llm: LLMClient,
) -> DecisionRoomState:
    """Run the sequential debate loop until max_debate_turns is reached."""
    state.current_phase = Phase.DEBATE

    for turn in range(1, state.max_debate_turns + 1):
        for agent in state.agents:
            chat_messages = _build_agent_messages(state, agent.system_prompt)

            reply = await llm.complete(chat_messages, tier=ModelTier.STANDARD)

            state.debate_transcript.append(
                Message(
                    agent_id=agent.agent_id,
                    role_title=agent.role_title,
                    content=reply,
                    phase=Phase.DEBATE,
                    turn_number=turn,
                )
            )

        state.debate_turn_count = turn

    return state


def _build_agent_messages(
    state: DecisionRoomState,
    system_prompt: str,
) -> list[dict[str, str]]:
    """Assemble the message list an agent sees during the debate."""
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": state.user_prompt},
    ]

    for msg in state.debate_transcript:
        messages.append({
            "role": "assistant",
            "content": f"[{msg.role_title}]: {msg.content}",
        })

    return messages
