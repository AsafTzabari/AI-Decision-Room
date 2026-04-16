"""Entry point for the Decision Room — FastAPI server or CLI one-shot."""

from __future__ import annotations

import asyncio
import logging
import sys

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

def create_app():
    """Build and return the FastAPI application."""
    from fastapi import FastAPI
    from pydantic import BaseModel

    app = FastAPI(title="Decision Room", version="0.1.0")

    class PromptRequest(BaseModel):
        prompt: str

    class DecisionResponse(BaseModel):
        session_id: str
        agents: list[dict]
        final_decision: str

    @app.post("/decide", response_model=DecisionResponse)
    async def decide(req: PromptRequest):
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
