"""Phase 3 — The Aggregator (Manager Pattern).

A static Master Agent receives all Expert Briefs and synthesizes them
into one cohesive final decision.  It does not debate — it weighs
contradictions and produces a "Best Of" output.
"""

from __future__ import annotations

from llm.client import LLMClient, ModelTier
from orchestrator.state import DecisionRoomState, Phase

_MASTER_SYSTEM = (
    "You are the Master Decision Synthesizer. You will receive independent "
    "Expert Briefs from multiple domain specialists who debated a question.\n\n"
    "Your task:\n"
    "1. Identify the key agreements and contradictions across the briefs.\n"
    "2. Weigh the strength of each expert's reasoning.\n"
    "3. Produce ONE cohesive, final decision that a non-expert user can act on.\n"
    "4. Clearly state which expert arguments you adopted, which you rejected, "
    "and why.\n\n"
    "Be decisive. Do not hedge. The user needs a clear recommendation."
)


async def run_aggregation(
    state: DecisionRoomState,
    llm: LLMClient,
) -> DecisionRoomState:
    """Feed expert briefs to the Master Agent for final synthesis."""
    state.current_phase = Phase.AGGREGATION

    briefs_text = _serialize_briefs(state)

    messages = [
        {"role": "system", "content": _MASTER_SYSTEM},
        {"role": "user", "content": (
            f"Original question:\n{state.user_prompt}\n\n"
            f"Expert Briefs:\n{briefs_text}"
        )},
    ]

    final = await llm.complete_with_retry(messages, tier=ModelTier.STANDARD)
    state.final_decision = final
    return state


def _serialize_briefs(state: DecisionRoomState) -> str:
    """Format expert briefs into a readable text block for the Master Agent."""
    sections: list[str] = []
    for i, brief in enumerate(state.expert_briefs, 1):
        sections.append(
            f"--- Expert {i}: {brief.role_title} ---\n{brief.content}\n"
        )
    return "\n".join(sections)
