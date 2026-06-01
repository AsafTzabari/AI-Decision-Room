"""API contract tests for the FastAPI app."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import create_app
from orchestrator.state import DecisionRoomState


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_openapi_and_docs_available(client: TestClient) -> None:
    openapi_response = client.get("/openapi.json")
    assert openapi_response.status_code == 200

    schema = openapi_response.json()
    assert schema["info"]["title"] == "Decision Room"
    assert "/decide" in schema["paths"]
    assert "/health" in schema["paths"]

    docs_response = client.get("/docs")
    assert docs_response.status_code == 200


def test_decide_happy_path_contract(client: TestClient, sample_agents) -> None:
    state = DecisionRoomState(
        user_prompt="Should we ship this release?",
        session_id="session-test-123",
        agents=sample_agents,
        final_decision="Ship with monitoring.",
    )

    with patch("main.SystemOrchestrator") as mock_orchestrator_cls:
        mock_orchestrator = mock_orchestrator_cls.return_value
        mock_orchestrator.run = AsyncMock(return_value=state)

        response = client.post("/decide", json={"prompt": "Should we ship?"})

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "session-test-123"
    assert body["final_decision"] == "Ship with monitoring."
    assert body["agents"] == [
        {"role_title": "Security Expert", "agent_id": "agent-1"},
        {"role_title": "Performance Engineer", "agent_id": "agent-2"},
    ]
    mock_orchestrator.run.assert_awaited_once_with("Should we ship?")


def test_decide_returns_empty_final_decision_when_none(
    client: TestClient, sample_agents
) -> None:
    state = DecisionRoomState(
        user_prompt="Should we ship this release?",
        session_id="session-test-empty",
        agents=sample_agents,
        final_decision=None,
    )

    with patch("main.SystemOrchestrator") as mock_orchestrator_cls:
        mock_orchestrator = mock_orchestrator_cls.return_value
        mock_orchestrator.run = AsyncMock(return_value=state)

        response = client.post("/decide", json={"prompt": "Decision?"})

    assert response.status_code == 200
    assert response.json()["final_decision"] == ""


def test_decide_requires_prompt(client: TestClient) -> None:
    response = client.post("/decide", json={})
    assert response.status_code == 422
