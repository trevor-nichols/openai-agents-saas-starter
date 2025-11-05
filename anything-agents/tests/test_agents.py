"""Test suite covering agent-facing endpoints and services."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from main import app
from app.domain.conversations import ConversationMessage
from app.services.agent_service import agent_service

client = TestClient(app)


def test_list_available_agents() -> None:
    response = client.get("/api/v1/agents")
    assert response.status_code == 200

    payload = response.json()
    assert isinstance(payload, list)
    assert any(agent["name"] == "triage" for agent in payload)


def test_get_agent_status() -> None:
    response = client.get("/api/v1/agents/triage/status")
    assert response.status_code == 200

    payload = response.json()
    assert payload["name"] == "triage"
    assert payload["status"] == "active"


def test_get_nonexistent_agent_status() -> None:
    response = client.get("/api/v1/agents/nonexistent/status")
    assert response.status_code == 404


@patch("app.infrastructure.openai.runner.run", new_callable=AsyncMock)
def test_chat_with_agent(mock_run: AsyncMock) -> None:
    mock_run.return_value = SimpleNamespace(final_output="Hello! I'm here to help you.")

    chat_request = {"message": "Hello, how are you?", "agent_type": "triage"}

    response = client.post("/api/v1/chat", json=chat_request)
    assert response.status_code == 200

    payload = response.json()
    assert payload["response"] == "Hello! I'm here to help you."
    assert payload["agent_used"] == "triage"
    assert payload["conversation_id"]


@patch("app.infrastructure.openai.runner.run", new_callable=AsyncMock)
def test_chat_falls_back_to_triage(mock_run: AsyncMock) -> None:
    mock_run.return_value = SimpleNamespace(final_output="Fallback engaged.")

    chat_request = {"message": "Route me", "agent_type": "nonexistent"}

    response = client.post("/api/v1/chat", json=chat_request)
    assert response.status_code == 200

    payload = response.json()
    assert payload["response"] == "Fallback engaged."
    assert payload["agent_used"] == "triage"


@patch("app.infrastructure.openai.runner.run", new_callable=AsyncMock)
def test_conversation_lifecycle(mock_run: AsyncMock) -> None:
    mock_run.return_value = SimpleNamespace(final_output="Sure, let's get started.")

    chat_request = {"message": "Start a new plan", "agent_type": "triage"}
    chat_response = client.post("/api/v1/chat", json=chat_request)
    assert chat_response.status_code == 200
    conversation_id = chat_response.json()["conversation_id"]

    history_response = client.get(f"/api/v1/conversations/{conversation_id}")
    assert history_response.status_code == 200
    history = history_response.json()
    assert history["conversation_id"] == conversation_id
    assert len(history["messages"]) >= 2

    list_response = client.get("/api/v1/conversations")
    assert list_response.status_code == 200
    conversations = list_response.json()
    assert any(item["conversation_id"] == conversation_id for item in conversations)

    delete_response = client.delete(f"/api/v1/conversations/{conversation_id}")
    assert delete_response.status_code == 204


def test_agent_service_initialization() -> None:
    agents = agent_service.list_available_agents()
    names = {agent.name for agent in agents}

    assert {"triage", "code_assistant", "data_analyst"}.issubset(names)


def test_conversation_repository_roundtrip() -> None:
    repository = agent_service.conversation_repository
    repository.clear_conversation("integration-test")

    repository.add_message(
        "integration-test",
        ConversationMessage(role="user", content="Test message"),
    )

    messages = repository.get_messages("integration-test")
    assert len(messages) == 1
    assert messages[0].content == "Test message"

    repository.clear_conversation("integration-test")
    assert repository.get_messages("integration-test") == []
