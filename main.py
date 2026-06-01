"""Entry point for the Decision Room — FastAPI server or CLI one-shot."""

from __future__ import annotations

import asyncio
import logging
import sys

from pydantic import BaseModel

from config import OrchestratorConfig
from orchestrator.engine import SystemOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)


# ---------------------------------------------------------------------------
# CLI mode
# ---------------------------------------------------------------------------

async def run_cli() -> None:
    """Interactive single-prompt CLI that runs the full pipeline."""
    print("\n=== Decision Room CLI ===")
    print("Enter your question and the multi-agent pipeline will analyze it.\n")

    try:
        user_input = input("Your question: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nExiting. Goodbye!")
        return

    if not user_input:
        print("No input provided. Exiting.")
        return

    orchestrator = SystemOrchestrator()
    state = await orchestrator.run(user_input)

    print("\n" + "=" * 72)
    print("RECRUITED AGENTS")
    print("=" * 72)
    for agent in state.agents:
        print(f"  - {agent.role_title}")

    print("\n" + "=" * 72)
    print("DEBATE TRANSCRIPT")
    print("=" * 72)
    for msg in state.debate_transcript:
        print(f"\n[Turn {msg.turn_number} — {msg.role_title}]")
        print(msg.content)

    print("\n" + "=" * 72)
    print("EXPERT BRIEFS")
    print("=" * 72)
    for brief in state.expert_briefs:
        print(f"\n--- {brief.role_title} ---")
        print(brief.content)

    print("\n" + "=" * 72)
    print("FINAL DECISION")
    print("=" * 72)
    print(state.final_decision)
    print()


# ---------------------------------------------------------------------------
# FastAPI mode
# ---------------------------------------------------------------------------

class PromptRequest(BaseModel):
    """Request body carrying the user's question for /decide."""

    prompt: str


class DecisionResponse(BaseModel):
    """Response body summarizing the pipeline outcome."""

    session_id: str
    agents: list[dict]
    final_decision: str


def create_app():
    """
    Create and configure the FastAPI application serving the Decision Room HTTP API.
    
    The returned app exposes:
    - POST /decide: accepts a `PromptRequest` JSON body, runs the decision pipeline, and returns a `DecisionResponse`.
    - GET /health: liveness endpoint that returns `{"status": "ok"}`.
    
    Returns:
        FastAPI: A configured FastAPI application instance.
    """
    from fastapi import FastAPI

    app = FastAPI(title="Decision Room", version="0.1.0")

    @app.post("/decide", response_model=DecisionResponse)
    async def decide(req: PromptRequest):
        """
        Run the decision pipeline for a prompt and produce a structured decision response.
        
        Parameters:
            req (PromptRequest): Request containing the user prompt to evaluate.
        
        Returns:
            DecisionResponse: Object containing `session_id`, `agents` (list of dicts with `role_title` and `agent_id`), and `final_decision` (empty string if no decision was produced).
        """
        orchestrator = SystemOrchestrator()
        state = await orchestrator.run(req.prompt)
        return DecisionResponse(
            session_id=state.session_id,
            agents=[
                {"role_title": a.role_title, "agent_id": a.agent_id}
                for a in state.agents
            ],
            final_decision=state.final_decision or "",
        )

    @app.get("/health")
    async def health():
        """Liveness probe returning a simple status payload."""
        return {"status": "ok"}

    return app


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if "--server" in sys.argv:
        import uvicorn

        uvicorn.run(create_app(), host="0.0.0.0", port=8000)
    else:
        asyncio.run(run_cli())
