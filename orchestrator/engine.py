"""SystemOrchestrator — runs the 4-phase pipeline from prompt to final decision."""

from __future__ import annotations

import logging

from config import OrchestratorConfig
from llm.client import LLMClient
from orchestrator.phases.phase0_recruiter import recruit_agents
from orchestrator.phases.phase1_chatroom import run_chatroom
from orchestrator.phases.phase2_independent import run_independent_briefs
from orchestrator.phases.phase3_aggregator import run_aggregation
from orchestrator.state import DecisionRoomState, Phase

logger = logging.getLogger(__name__)


class SystemOrchestrator:
    """Runs Phases 0 through 3 sequentially and returns the final state."""

    def __init__(self, config: OrchestratorConfig | None = None) -> None:
        """Initialize with the given config (or load it from the env)."""
        self.config = config or OrchestratorConfig.from_env()
        self.llm = LLMClient(self.config)

    async def run(self, user_prompt: str) -> DecisionRoomState:
        """Execute Phases 0-3 for the prompt and return the final state."""
        state = DecisionRoomState(
            user_prompt=user_prompt,
            max_debate_turns=self.config.max_debate_turns,
        )

        logger.info("[%s] Phase 0: Recruiting agents...", state.session_id)
        state = await recruit_agents(state, self.llm, self.config)
        logger.info(
            "[%s] Recruited %d agents: %s",
            state.session_id,
            len(state.agents),
            [a.role_title for a in state.agents],
        )

        logger.info("[%s] Phase 1: Starting debate (%d turns)...", state.session_id, state.max_debate_turns)
        state = await run_chatroom(state, self.llm)
        logger.info("[%s] Debate complete — %d messages.", state.session_id, len(state.debate_transcript))

        state.freeze_transcript()
        logger.info("[%s] Transcript frozen.", state.session_id)

        logger.info("[%s] Phase 2: Generating independent briefs...", state.session_id)
        state = await run_independent_briefs(state, self.llm)
        logger.info("[%s] Collected %d expert briefs.", state.session_id, len(state.expert_briefs))

        logger.info("[%s] Phase 3: Master Agent aggregation...", state.session_id)
        state = await run_aggregation(state, self.llm)

        state.current_phase = Phase.COMPLETE
        logger.info("[%s] Pipeline complete.", state.session_id)
        return state
