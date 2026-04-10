---
name: Decision Room Refactor
overview: Refactor the current single-call Python CLI into a 4-phase multi-agent orchestration architecture, with Python as the canonical backend runtime and TypeScript interfaces at the API/UI boundary.
todos:
  - id: define-domain-models
    content: Define canonical Python state models for sessions, agents, transcript messages, expert briefs, and final decisions.
    status: pending
  - id: split-orchestrator-phases
    content: Create explicit phase modules for recruiter, debate loop, swarm synthesis, and final aggregation under a single orchestrator package.
    status: pending
  - id: stabilize-llm-boundary
    content: Preserve LiteLLM access behind a dedicated client/router layer with schema validation and prompt assembly separated from orchestration logic.
    status: pending
  - id: add-concurrency-and-snapshots
    content: Design mutex-protected Phase 1 turn-taking and immutable transcript freezing before Phase 2 parallel execution.
    status: pending
  - id: publish-ts-contracts
    content: Mirror the stable backend DTOs into TypeScript interfaces for any future API or frontend integration.
    status: pending
isProject: false
---

# Decision Room Refactor Plan

## Current Baseline

The current workspace is a minimal Python implementation built around `[main.py](main.py)` and `[llm_client.py](llm_client.py)`:

- `[main.py](main.py)` owns a flat in-memory `messages` list and a single request loop.
- `[llm_client.py](llm_client.py)` is the low-level LiteLLM adapter and should remain the provider boundary after the refactor.

This means the new architecture should be introduced as an additive orchestration package, not as a tweak to the current request loop.

## Proposed Directory Structure

Use Python as the orchestration source of truth, and expose mirrored TypeScript contracts for any API/frontend layer.

```text
atc/
  main.py                       # thin CLI bootstrap, delegates to orchestrator
  llm_client.py                 # kept temporarily or moved behind llm/client.py
  decision_room/
    __init__.py
    entrypoints/
      cli.py                    # terminal entrypoint
      api.py                    # optional future HTTP/FastAPI boundary
    orchestrator/
      system_orchestrator.py    # 4-phase coordinator / state machine
      phases/
        recruiter.py            # Phase 0: dynamic team assembly
        debate_loop.py          # Phase 1: shared chat room loop
        independent_swarm.py    # Phase 2: parallel isolated briefs
        aggregator.py           # Phase 3: master synthesis
      policies/
        cognitive_framework.py  # hardcoded global rule injection
        stop_criteria.py        # exact 3-4 turn enforcement
        turn_lock.py            # mutex / concurrency guard
    agents/
      models.py                 # AgentDefinition, AgentRuntimeConfig
      factory.py                # instantiates recruited agents + master agent
      prompts.py                # persona composition and prompt builders
    state/
      models.py                 # SessionState, Transcript, Brief, FinalDecision
      enums.py                  # Phase, MessageVisibility, AgentKind
      store.py                  # in-memory state repository abstraction
      reducers.py               # pure phase transition helpers
      snapshots.py              # frozen transcript creation
    llm/
      client.py                 # provider-agnostic completion wrapper
      schemas.py                # structured JSON contracts / validation
      guards.py                 # JSON parsing, retries, validation failures
      model_router.py           # recruiter vs expert vs master model selection
    interfaces/
      python/
        protocols.py            # Protocols / ABCs for orchestrator and clients
      typescript/
        decision-room.ts        # DTOs for API/frontend consumers
    tests/
      unit/
      integration/
```

## State Management Approach

Use one canonical `DecisionSessionState` object per user request. Treat it as an append-only workflow state with explicit phase transitions instead of mutating ad hoc dictionaries.

### Core approach

- Store the recruited team as `agents: AgentDefinition[]`, so variable team size `n` is naturally handled as a collection rather than fixed slots.
- Keep Phase 1 discussion in `sharedTranscript: TranscriptMessage[]`.
- Protect Phase 1 writes with a server-side lock (`asyncio.Lock` in Python for the first version) so only one agent appends to shared memory at a time.
- When the debate reaches the stop criterion, create an immutable `frozenTranscript` snapshot from `sharedTranscript`.
- Launch Phase 2 as parallel tasks over that same immutable snapshot; each agent writes to its own `expertBrief` record, never back into shared transcript.
- Feed the collected `expertBriefs: ExpertBrief[]` into the static master agent in Phase 3.
- Persist phase metadata such as `currentPhase`, `loopIteration`, `maxIterations`, timestamps, and execution status per agent so retries and observability stay deterministic.

### Why this fits variable agent counts

A variable number of agents is easiest to manage with list/map structures keyed by `agentId`:

- `agents: AgentDefinition[]`
- `sharedTranscript: TranscriptMessage[]`
- `expertBriefsByAgentId: dict[str, ExpertBrief]` in Python
- `expertBriefsByAgentId: Record<string, ExpertBrief>` in TypeScript

That avoids hardcoding slots like `agent1`, `agent2`, `agent3` and keeps the orchestrator generic for `n = 2..4`.

### Recommended state transition model

Use a reducer/state-machine style API:

- `assembleTeam(state, recruiterOutput) -> state`
- `appendDebateTurn(state, message) -> state`
- `freezeTranscript(state) -> state`
- `attachExpertBrief(state, brief) -> state`
- `finalizeDecision(state, finalDecision) -> state`

This keeps the orchestration logic explicit and makes Phase 1 -> 2 -> 3 handoff testable.

## Pseudo-Code Interfaces

Assumption: Python is the execution/runtime layer; TypeScript definitions mirror the backend contract for future API/UI integration.

### Python

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal, Protocol

class Phase(str, Enum):
    RECRUIT = "recruit"
    DEBATE = "debate"
    SWARM = "swarm"
    AGGREGATE = "aggregate"
    COMPLETE = "complete"

class AgentKind(str, Enum):
    RECRUITER = "recruiter"
    EXPERT = "expert"
    MASTER = "master"

@dataclass(frozen=True)
class AgentDefinition:
    agent_id: str
    kind: AgentKind
    role_title: str
    base_persona: str
    injected_persona: str

@dataclass(frozen=True)
class TranscriptMessage:
    message_id: str
    phase: Phase
    speaker_agent_id: str | None
    role: Literal["system", "user", "assistant", "agent"]
    content: str
    turn_index: int
    iteration: int
    visible_to_all: bool = True

@dataclass(frozen=True)
class ExpertBrief:
    agent_id: str
    role_title: str
    conclusion: str
    supporting_points: list[str]
    contradictions_found: list[str]

@dataclass(frozen=True)
class FinalDecision:
    summary: str
    best_of_decision: str
    rationale: list[str]
    source_agent_ids: list[str]

@dataclass
class DecisionSessionState:
    session_id: str
    user_prompt: str
    current_phase: Phase
    max_iterations: int
    loop_iteration: int = 0
    agents: list[AgentDefinition] = field(default_factory=list)
    shared_transcript: list[TranscriptMessage] = field(default_factory=list)
    frozen_transcript: list[TranscriptMessage] = field(default_factory=list)
    expert_briefs: list[ExpertBrief] = field(default_factory=list)
    final_decision: FinalDecision | None = None

class AgentRunner(Protocol):
    async def run(self, agent: AgentDefinition, messages: list[TranscriptMessage]) -> str: ...

class RecruiterRunner(Protocol):
    async def recruit(self, user_prompt: str) -> list[AgentDefinition]: ...

class SystemOrchestrator(Protocol):
    async def execute(self, user_prompt: str) -> FinalDecision: ...
    async def run_phase_0_recruiter(self, state: DecisionSessionState) -> DecisionSessionState: ...
    async def run_phase_1_debate(self, state: DecisionSessionState) -> DecisionSessionState: ...
    async def run_phase_2_swarm(self, state: DecisionSessionState) -> DecisionSessionState: ...
    async def run_phase_3_aggregate(self, state: DecisionSessionState) -> DecisionSessionState: ...
```

### TypeScript

```ts
export type Phase = 'recruit' | 'debate' | 'swarm' | 'aggregate' | 'complete';
export type AgentKind = 'recruiter' | 'expert' | 'master';
export type MessageRole = 'system' | 'user' | 'assistant' | 'agent';

export interface AgentDefinition {
  agentId: string;
  kind: AgentKind;
  roleTitle: string;
  basePersona: string;
  injectedPersona: string;
}

export interface TranscriptMessage {
  messageId: string;
  phase: Phase;
  speakerAgentId: string | null;
  role: MessageRole;
  content: string;
  turnIndex: number;
  iteration: number;
  visibleToAll: boolean;
}

export interface ExpertBrief {
  agentId: string;
  roleTitle: string;
  conclusion: string;
  supportingPoints: string[];
  contradictionsFound: string[];
}

export interface FinalDecision {
  summary: string;
  bestOfDecision: string;
  rationale: string[];
  sourceAgentIds: string[];
}

export interface DecisionSessionState {
  sessionId: string;
  userPrompt: string;
  currentPhase: Phase;
  maxIterations: number;
  loopIteration: number;
  agents: AgentDefinition[];
  sharedTranscript: TranscriptMessage[];
  frozenTranscript: TranscriptMessage[];
  expertBriefs: ExpertBrief[];
  finalDecision: FinalDecision | null;
}

export interface SystemOrchestrator {
  execute(userPrompt: string): Promise<FinalDecision>;
  runPhase0Recruiter(state: DecisionSessionState): Promise<DecisionSessionState>;
  runPhase1Debate(state: DecisionSessionState): Promise<DecisionSessionState>;
  runPhase2Swarm(state: DecisionSessionState): Promise<DecisionSessionState>;
  runPhase3Aggregate(state: DecisionSessionState): Promise<DecisionSessionState>;
}
```

## Architectural Defaults I Recommend

- Keep the orchestration runtime in Python first, because the existing codebase is Python-only today.
- Treat TypeScript as the contract layer for future API/frontend consumers rather than making the orchestration itself hybrid on day one.
- Keep `llm_client.py` or its successor in `decision_room/llm/client.py` as the only direct LLM provider boundary.
- Make recruiter output schema-validated JSON before agent instantiation.
- Inject the hardcoded cognitive framework in backend code only, never delegate it to the recruiter model.
- Freeze transcript by snapshot copy before swarm execution so Phase 2 remains fully isolated and reproducible.

## Likely First Implementation Slice

1. Extract the current single-call flow from `[main.py](main.py)` into a `decision_room/entrypoints/cli.py` wrapper.
2. Move LLM access behind `decision_room/llm/client.py` while preserving the current LiteLLM behavior from `[llm_client.py](llm_client.py)`.
3. Introduce typed state models and a minimal `SystemOrchestrator` that can execute the 4-phase pipeline without changing providers yet.
4. Add JSON validation for recruiter responses and immutable transcript freezing before parallel swarm execution.
5. Add mirrored TypeScript DTOs once the Python domain model is stable.

