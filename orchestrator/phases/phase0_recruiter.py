"""Phase 0 — Dynamic Team Assembly (The Recruiter).

Sends the user prompt to a fast/cheap LLM and gets back 2-4 expert
agent definitions.  The orchestrator then injects the hardcoded
Cognitive Framework into each agent's system prompt.
"""

from __future__ import annotations

import uuid

from agents.cognitive_framework import build_system_prompt
from agents.models import AgentDefinition
from config import OrchestratorConfig
from llm.client import LLMClient, ModelTier
from orchestrator.state import DecisionRoomState, Phase

_RECRUITER_SYSTEM = (
    "You are the Recruiter. Given a user's question, generate a team of "
    "expert agents who will debate and analyze it.\n\n"
    "RULES:\n"
    "- Return a JSON array with 2 to 4 objects.\n"
    "- Each object MUST have exactly two keys:\n"
    '  - "role_title": a concise expert title (e.g. "Cloud Security Architect")\n'
    '  - "base_persona": a 2-3 sentence persona description starting with "You are..."\n'
    "- Return ONLY the JSON array. No markdown fences, no explanation."
)


async def recruit_agents(
    state: DecisionRoomState,
    llm: LLMClient,
    config: OrchestratorConfig,
) -> DecisionRoomState:
    """Call the Recruiter LLM, parse its JSON, inject cognitive rules."""
    state.current_phase = Phase.RECRUITING

    messages = [
        {"role": "system", "content": _RECRUITER_SYSTEM},
        {"role": "user", "content": state.user_prompt},
    ]

    raw = await llm.complete_json(messages, tier=ModelTier.FAST)

    if not isinstance(raw, list) or not (config.min_agents <= len(raw) <= config.max_agents):
        raise ValueError(
            f"Recruiter returned {len(raw) if isinstance(raw, list) else type(raw).__name__} "
            f"agents; expected {config.min_agents}-{config.max_agents}."
        )

    agents: list[AgentDefinition] = []
    for entry in raw:
        agent = AgentDefinition(
            agent_id=str(uuid.uuid4()),
            role_title=entry["role_title"],
            base_persona=entry["base_persona"],
            system_prompt=build_system_prompt(entry["base_persona"]),
        )
        agents.append(agent)

    state.agents = agents
    return state
