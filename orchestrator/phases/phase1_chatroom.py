"""Phase 1 — The Chat Room (Loop Pattern).

Agents debate sequentially over 3-4 rounds.  Each agent sees the full
chat history so far and must critique the previous message before adding
its own analysis (enforced by the Cognitive Framework in its system prompt).

The transcript is delivered as plain text inside a single ``user`` message
rather than as a stack of synthetic ``assistant`` messages.  Multiple
``assistant`` turns can be misread by chat-completion providers as a single
ongoing assistant reply, causing later agents to return empty content.
A single ``user`` instruction with an explicit "you are <role>, write your
turn now" directive avoids that ambiguity.
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
            chat_messages = _build_agent_messages(
                state=state,
                system_prompt=agent.system_prompt,
                role_title=agent.role_title,
                turn=turn,
            )

            reply = await llm.complete_with_retry(
                chat_messages, tier=ModelTier.STANDARD
            )

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
    role_title: str,
    turn: int,
) -> list[dict[str, str]]:
    """Assemble the message list an agent sees during the debate.

    The shape is intentionally minimal:
        - system: agent persona + cognitive rules
        - user:   original question + transcript so far + speaking instruction

    No synthetic ``assistant`` turns are sent.
    """
    transcript_block = _format_transcript(state)
    is_first_speaker = len(state.debate_transcript) == 0

    if is_first_speaker:
        speaking_instruction = (
            f"You are speaking first as the {role_title} on Turn {turn}.\n"
            "There are no prior debate messages yet.\n\n"
            "Provide your initial analysis of the question.  Identify the key "
            "assumptions, risks, or unstated constraints embedded in the "
            "question itself, then deliver your substantive contribution.\n\n"
            "Respond ONLY as the expert.  Do not ask the user follow-up "
            "questions, do not return an empty message, and do not preface "
            "your reply with meta commentary about the debate format."
        )
    else:
        speaking_instruction = (
            f"You are now speaking as the {role_title} on Turn {turn}.\n\n"
            "First, identify at least one logical flaw, unstated assumption, "
            "or risk in the most recent prior message.  Then add your own "
            "substantive analysis from your area of expertise.\n\n"
            "Respond ONLY as the expert.  Do not ask the user follow-up "
            "questions, do not return an empty message, and do not preface "
            "your reply with meta commentary about the debate format."
        )

    user_block = (
        f"Original question:\n{state.user_prompt}\n\n"
        f"Debate transcript so far:\n{transcript_block}\n\n"
        f"{speaking_instruction}"
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_block},
    ]


def _format_transcript(state: DecisionRoomState) -> str:
    """Render the running debate transcript as readable plain text."""
    if not state.debate_transcript:
        return "(no messages yet)"

    lines: list[str] = []
    for msg in state.debate_transcript:
        lines.append(f"[Turn {msg.turn_number} — {msg.role_title}]\n{msg.content}")
    return "\n\n".join(lines)
