"""Test suite covering agent-facing endpoints and services."""

import os
from datetime import UTC, datetime
from typing import cast
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("RATE_LIMIT_REDIS_URL", os.environ["REDIS_URL"])
os.environ.setdefault("AUTH_CACHE_REDIS_URL", os.environ["REDIS_URL"])
os.environ.setdefault("SECURITY_TOKEN_REDIS_URL", os.environ["REDIS_URL"])
os.environ.setdefault("ENABLE_BILLING", "false")
os.environ.setdefault("ENABLE_USAGE_GUARDRAILS", "false")

pytestmark = pytest.mark.auto_migrations(enabled=True)

from app.api.dependencies import usage as usage_dependencies  # noqa: E402
from app.api.dependencies.auth import require_current_user  # noqa: E402
from app.api.v1.chat import router as chat_router  # noqa: E402
from app.api.v1.chat.schemas import AgentChatResponse  # noqa: E402
from app.bootstrap.container import get_container  # noqa: E402
from app.domain.ai import AgentRunResult  # noqa: E402
from app.domain.conversations import ConversationMessage, ConversationMetadata  # noqa: E402
from app.services.agent_service import agent_service  # noqa: E402
from app.services.shared.rate_limit_service import RateLimitExceeded, rate_limiter  # noqa: E402
from app.services.usage_policy_service import (  # noqa: E402
    UsagePolicyDecision,
    UsagePolicyResult,
    UsagePolicyService,
    UsageViolation,
)
from main import app  # noqa: E402

TEST_TENANT_ID = str(uuid4())


def _stub_current_user():
    return {
        "user_id": "test-user",
        "subject": "user:test-user",
        "payload": {
            "scope": "conversations:read conversations:write conversations:delete tools:read",
            "tenant_id": TEST_TENANT_ID,
            "roles": ["admin"],
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


@pytest.fixture(scope="function")
def client(_configure_agent_provider):
    with TestClient(app) as test_client:
        yield test_client


def test_list_available_agents(client: TestClient) -> None:
    response = client.get("/api/v1/agents")
    assert response.status_code == 200

    payload = response.json()
    assert isinstance(payload, list)
    assert any(agent["name"] == "triage" for agent in payload)


def test_get_agent_status(client: TestClient) -> None:
    response = client.get("/api/v1/agents/triage/status")
    assert response.status_code == 200

    payload = response.json()
    assert payload["name"] == "triage"
    assert payload["status"] == "active"


def test_get_nonexistent_agent_status(client: TestClient) -> None:
    response = client.get("/api/v1/agents/nonexistent/status")
    assert response.status_code == 404


@patch("app.infrastructure.providers.openai.runtime.Runner.run", new_callable=AsyncMock)
def test_chat_with_agent(mock_run: AsyncMock, client: TestClient) -> None:
    mock_run.return_value = AgentRunResult(
        final_output="Hello! I'm here to help you.",
        response_id="resp",
        usage=None,
        metadata=None,
    )

    chat_request = {"message": "Hello, how are you?", "agent_type": "triage"}

    response = client.post("/api/v1/chat", json=chat_request)
    assert response.status_code == 200

    payload = response.json()
    assert payload["response"] == "Hello! I'm here to help you."
    assert payload["agent_used"] == "triage"
    assert payload["conversation_id"]


@patch("app.infrastructure.providers.openai.runtime.Runner.run", new_callable=AsyncMock)
def test_chat_falls_back_to_triage(mock_run: AsyncMock, client: TestClient) -> None:
    mock_run.return_value = AgentRunResult(
        final_output="Fallback engaged.",
        response_id="resp",
        usage=None,
        metadata=None,
    )

    chat_request = {"message": "Route me", "agent_type": "nonexistent"}

    response = client.post("/api/v1/chat", json=chat_request)
    assert response.status_code == 200

    payload = response.json()
    assert payload["response"] == "Fallback engaged."
    assert payload["agent_used"] == "triage"


@patch("app.infrastructure.providers.openai.runtime.Runner.run", new_callable=AsyncMock)
def test_conversation_lifecycle(mock_run: AsyncMock, client: TestClient) -> None:
    mock_run.return_value = AgentRunResult(
        final_output="Sure, let's get started.",
        response_id="resp",
        usage=None,
        metadata=None,
    )

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
    list_payload = list_response.json()
    assert "items" in list_payload
    conversations = list_payload["items"]
    assert any(item["conversation_id"] == conversation_id for item in conversations)

    delete_response = client.delete(f"/api/v1/conversations/{conversation_id}")
    assert delete_response.status_code == 204


def test_agent_service_initialization() -> None:
    agents = agent_service.list_available_agents()
    names = {agent.name for agent in agents}

    assert {"triage", "code_assistant", "data_analyst"}.issubset(names)


def test_chat_requires_write_scope(client: TestClient) -> None:
    def _read_only_user():
        return {
            "user_id": "limited",
            "subject": "user:limited",
            "payload": {
                "scope": "conversations:read",
                "tenant_id": TEST_TENANT_ID,
                "roles": ["admin"],
            },
        }

    app.dependency_overrides[require_current_user] = _read_only_user
    try:
        response = client.post("/api/v1/chat", json={"message": "hi"})
        assert response.status_code == 403
    finally:
        app.dependency_overrides[require_current_user] = _stub_current_user


def test_delete_requires_delete_scope(client: TestClient) -> None:
    def _no_delete_user():
        return {
            "user_id": "limited",
            "subject": "user:limited",
            "payload": {
                "scope": "conversations:read conversations:write",
                "tenant_id": TEST_TENANT_ID,
                "roles": ["admin"],
            },
        }

    app.dependency_overrides[require_current_user] = _no_delete_user
    try:
        response = client.delete("/api/v1/conversations/test-id")
        assert response.status_code == 403
    finally:
        app.dependency_overrides[require_current_user] = _stub_current_user


def test_chat_rate_limit_blocks(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    class _SettingsStub:
        chat_rate_limit_per_minute = 1
        chat_stream_rate_limit_per_minute = 1
        chat_stream_concurrent_limit = 1

    invocation = {"count": 0}

    async def _fake_enforce(quota, _key_parts):
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

    async def _fake_chat(_request, *, actor):
        return AgentChatResponse(
            response="ok",
            conversation_id="rate-test",
            agent_used="triage",
        )

    monkeypatch.setattr(agent_service, "chat", _fake_chat)

    first = client.post("/api/v1/chat", json={"message": "hi"})
    assert first.status_code == 200

    second = client.post("/api/v1/chat", json={"message": "still hi"})
    assert second.status_code == 429
    assert "Rate limit exceeded" in second.text


@patch("app.infrastructure.providers.openai.runtime.Runner.run", new_callable=AsyncMock)
def test_chat_blocks_when_usage_guardrail_hits(
    mock_run: AsyncMock, monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    class _SettingsStub:
        enable_usage_guardrails = True

    violation = UsageViolation(
        feature_key="messages",
        limit_type="hard_limit",
        limit_value=100,
        usage=150,
        unit="messages",
        window_start=datetime.now(UTC),
        window_end=datetime.now(UTC),
    )
    result = UsagePolicyResult(
        decision=UsagePolicyDecision.HARD_LIMIT,
        window_start=datetime.now(UTC),
        window_end=datetime.now(UTC),
        violations=[violation],
    )

    class _StubUsagePolicyService:
        async def evaluate(self, tenant_id: str):
            return result

    monkeypatch.setattr(usage_dependencies, "get_settings", lambda: _SettingsStub())
    container = get_container()
    previous_service = container.usage_policy_service
    container.usage_policy_service = cast(UsagePolicyService, _StubUsagePolicyService())

    response = client.post("/api/v1/chat", json={"message": "hello"})
    try:
        assert response.status_code == 429
        payload = response.json()
        assert payload["detail"]["feature_key"] == "messages"
    finally:
        container.usage_policy_service = previous_service

@pytest.mark.asyncio
async def test_conversation_repository_roundtrip() -> None:
    repository = agent_service.conversation_repository
    await repository.clear_conversation("integration-test", tenant_id=TEST_TENANT_ID)

    await repository.add_message(
        "integration-test",
        ConversationMessage(role="user", content="Test message"),
        tenant_id=TEST_TENANT_ID,
        metadata=ConversationMetadata(tenant_id=TEST_TENANT_ID, agent_entrypoint="triage"),
    )

    messages = await repository.get_messages("integration-test", tenant_id=TEST_TENANT_ID)
    assert len(messages) == 1
    assert messages[0].content == "Test message"

    await repository.clear_conversation("integration-test", tenant_id=TEST_TENANT_ID)
    assert await repository.get_messages("integration-test", tenant_id=TEST_TENANT_ID) == []


def test_chat_missing_tenant_claim_rejected(client: TestClient) -> None:
    def _missing_tenant_user():
        return {
            "user_id": "no-tenant",
            "subject": "user:no-tenant",
            "payload": {"scope": "conversations:write"},
        }

    app.dependency_overrides[require_current_user] = _missing_tenant_user
    try:
        response = client.post("/api/v1/chat", json={"message": "hi"})
        assert response.status_code == 401
    finally:
        app.dependency_overrides[require_current_user] = _stub_current_user
