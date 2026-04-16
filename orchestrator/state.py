"""DecisionRoomState — single source of truth for the pipeline run."""

from __future__ import annotations

import uuid
from copy import deepcopy
from enum import Enum

from pydantic import BaseModel, Field

from agents.models import AgentDefinition, ExpertBrief


class Phase(str, Enum):
    RECRUITING = "recruiting"
    DEBATE = "debate"
    INDEPENDENT = "independent"
    AGGREGATION = "aggregation"
    COMPLETE = "complete"


class Message(BaseModel):
    """A single message in the debate transcript."""

    agent_id: str
    role_title: str
    content: str
    phase: Phase
    turn_number: int


class DecisionRoomState(BaseModel):
    """Tracks every artefact produced across the four phases."""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_prompt: str

    # Phase 0 output
    agents: list[AgentDefinition] = []

    # Phase 1 output
    debate_transcript: list[Message] = []
    debate_turn_count: int = 0
    max_debate_turns: int = 3

    # Phase 1 -> Phase 2 boundary
    frozen_transcript: list[Message] | None = None

    # Phase 2 output
    expert_briefs: list[ExpertBrief] = []

    # Phase 3 output
    final_decision: str | None = None

    current_phase: Phase = Phase.RECRUITING

    def freeze_transcript(self) -> None:
        """Deep-copy the debate transcript so Phase 2 agents get an immutable snapshot."""
        self.frozen_transcript = deepcopy(self.debate_transcript)
        self.current_phase = Phase.INDEPENDENT

    def transcript_as_messages(self) -> list[dict[str, str]]:
        """Serialize the frozen transcript into the chat-completion message format."""
        if self.frozen_transcript is None:
            raise ValueError("Transcript has not been frozen yet.")
        return [
            {"role": "assistant", "content": f"[{m.role_title}]: {m.content}"}
            for m in self.frozen_transcript
        ]
