"""Test suite covering agent-facing endpoints and services."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import os
import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("AUTO_RUN_MIGRATIONS", "false")
os.environ.setdefault("ENABLE_BILLING", "false")

from app.api.dependencies.auth import require_current_user
from app.api.v1.chat import router as chat_router
from app.api.v1.chat.schemas import AgentChatResponse
from app.domain.conversations import ConversationMessage, ConversationMetadata
from app.services.agent_service import agent_service
from app.services.rate_limit_service import RateLimitExceeded, rate_limiter
from main import app

client = TestClient(app)


def _stub_current_user():
    return {
        "user_id": "test-user",
        "subject": "user:test-user",
        "payload": {
            "scope": "conversations:read conversations:write conversations:delete tools:read",
        },
    }


@pytest.fixture(autouse=True)
def _override_current_user():
    """Scope the auth override to this module so other suites see real auth."""

    previous = app.dependency_overrides.get(require_current_user)
    app.dependency_overrides[require_current_user] = _stub_current_user
    try:
        yield
    finally:
        if previous is None:
            app.dependency_overrides.pop(require_current_user, None)
        else:
            app.dependency_overrides[require_current_user] = previous


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


def test_chat_requires_write_scope() -> None:
    def _read_only_user():
        return {
            "user_id": "limited",
            "subject": "user:limited",
            "payload": {"scope": "conversations:read"},
        }

    app.dependency_overrides[require_current_user] = _read_only_user
    try:
        response = client.post("/api/v1/chat", json={"message": "hi"})
        assert response.status_code == 403
    finally:
        app.dependency_overrides[require_current_user] = _stub_current_user


def test_delete_requires_delete_scope() -> None:
    def _no_delete_user():
        return {
            "user_id": "limited",
            "subject": "user:limited",
            "payload": {"scope": "conversations:read conversations:write"},
        }

    app.dependency_overrides[require_current_user] = _no_delete_user
    try:
        response = client.delete("/api/v1/conversations/test-id")
        assert response.status_code == 403
    finally:
        app.dependency_overrides[require_current_user] = _stub_current_user


def test_chat_rate_limit_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    class _SettingsStub:
        chat_rate_limit_per_minute = 1
        chat_stream_rate_limit_per_minute = 1
        chat_stream_concurrent_limit = 1

    invocation = {"count": 0}

    async def _fake_enforce(quota, key_parts):  # type: ignore[unused-argument]
        invocation["count"] += 1
        if invocation["count"] > quota.limit:
            raise RateLimitExceeded(
                quota=quota.name,
                limit=quota.limit,
                retry_after=60,
                scope=quota.scope,
            )

    monkeypatch.setattr(rate_limiter, "enforce", _fake_enforce)
    monkeypatch.setattr(chat_router, "get_settings", lambda: _SettingsStub())

    async def _fake_chat(request):  # type: ignore[unused-argument]
        return AgentChatResponse(
            response="ok",
            conversation_id="rl-test",
            agent_used="triage",
        )

    monkeypatch.setattr(agent_service, "chat", _fake_chat)

    first = client.post("/api/v1/chat", json={"message": "hello"})
    assert first.status_code == 200

    second = client.post("/api/v1/chat", json={"message": "hello again"})
    assert second.status_code == 429
    assert "Rate limit exceeded" in second.text


@pytest.mark.asyncio
async def test_conversation_repository_roundtrip() -> None:
    repository = agent_service.conversation_repository
    await repository.clear_conversation("integration-test")

    await repository.add_message(
        "integration-test",
        ConversationMessage(role="user", content="Test message"),
        metadata=ConversationMetadata(agent_entrypoint="triage"),
    )

    messages = await repository.get_messages("integration-test")
    assert len(messages) == 1
    assert messages[0].content == "Test message"

    await repository.clear_conversation("integration-test")
    assert await repository.get_messages("integration-test") == []
