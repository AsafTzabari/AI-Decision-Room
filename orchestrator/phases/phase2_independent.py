"""Phase 2 — Independent Answers (Swarm Pattern).

Each agent receives the frozen transcript and independently produces
an Expert Brief.  Agents are fully isolated — they cannot see what
the others are writing.  All calls run in parallel via asyncio.gather.
"""

from __future__ import annotations

import asyncio

from agents.models import ExpertBrief
from llm.client import LLMClient, ModelTier
from orchestrator.state import DecisionRoomState, Phase

_BRIEF_INSTRUCTION = (
    "You have just participated in a multi-expert debate. Below is the "
    "full transcript. Now, working INDEPENDENTLY, produce your final Expert "
    "Brief: a clear, structured conclusion that reflects YOUR unique expertise. "
    "Weigh all arguments from the debate, call out the strongest and weakest "
    "points, and deliver a decisive recommendation."
)


async def run_independent_briefs(
    state: DecisionRoomState,
    llm: LLMClient,
) -> DecisionRoomState:
    """Dispatch frozen transcript to all agents in parallel."""
    state.current_phase = Phase.INDEPENDENT

    transcript_text = _serialize_transcript(state)

    tasks = [
        _generate_brief(agent_def, transcript_text, state.user_prompt, llm)
        for agent_def in state.agents
    ]

    briefs: list[ExpertBrief] = await asyncio.gather(*tasks)
    state.expert_briefs = briefs
    return state


async def _generate_brief(
    agent_def,
    transcript_text: str,
    user_prompt: str,
    llm: LLMClient,
) -> ExpertBrief:
    """Single agent producing its isolated Expert Brief."""
    messages = [
        {"role": "system", "content": agent_def.system_prompt},
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": transcript_text},
        {"role": "user", "content": _BRIEF_INSTRUCTION},
    ]

    content = await llm.complete(messages, tier=ModelTier.STANDARD)

    return ExpertBrief(
        agent_id=agent_def.agent_id,
        role_title=agent_def.role_title,
        content=content,
    )


def _serialize_transcript(state: DecisionRoomState) -> str:
    """Turn the frozen transcript into a readable text block."""
    if state.frozen_transcript is None:
        raise ValueError("Transcript has not been frozen yet.")

    lines: list[str] = []
    for msg in state.frozen_transcript:
        lines.append(f"[Turn {msg.turn_number} — {msg.role_title}]\n{msg.content}\n")
    return "\n".join(lines)
