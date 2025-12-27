"""Contract tests for chat endpoints (non-streaming)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from tests.utils.contract_auth import make_user_payload, override_current_user
from tests.utils.contract_env import TEST_TENANT_ID, configure_contract_env

configure_contract_env()

pytestmark = pytest.mark.auto_migrations(enabled=True)

from app.api.dependencies import usage as usage_dependencies  # noqa: E402
from app.api.v1.chat import router as chat_router  # noqa: E402
from app.api.v1.chat.schemas import AgentChatResponse  # noqa: E402
from app.infrastructure.db.engine import init_engine  # noqa: E402
from app.services.shared.rate_limit_service import RateLimitExceeded, rate_limiter  # noqa: E402
from app.services.usage.policy_service import (  # noqa: E402
    UsagePolicyDecision,
    UsagePolicyResult,
    UsagePolicyService,
    UsageViolation,
)
from app.bootstrap.container import get_container  # noqa: E402
from app.domain.ai import AgentRunResult  # noqa: E402
from main import app  # noqa: E402
from tests.utils.agent_contract import (  # noqa: E402
    default_agent_key,
    expected_output_schema,
    schema_agent_key,
)


def _stub_current_user() -> dict[str, Any]:
    return make_user_payload()


@pytest_asyncio.fixture(autouse=True)
async def _ensure_engine_initialized() -> None:
    await init_engine(run_migrations=True)


@pytest.fixture(autouse=True)
def _override_current_user():
    with override_current_user(app, _stub_current_user):
        yield


@pytest.fixture(scope="function")
def client(_configure_agent_provider):
    with TestClient(app) as test_client:
        yield test_client


@patch(
    "app.infrastructure.providers.openai.runtime.OpenAIAgentRuntime.run",
    new_callable=AsyncMock,
)
def test_chat_with_agent(mock_run: AsyncMock, client: TestClient) -> None:
    mock_run.return_value = AgentRunResult(
        final_output="Hello! I'm here to help you.",
        response_id="resp",
        usage=None,
        metadata=None,
    )

    agent_key = default_agent_key()
    chat_request = {"message": "Hello, how are you?", "agent_type": agent_key}

    response = client.post("/api/v1/chat", json=chat_request)
    assert response.status_code == 200

    payload = response.json()
    assert payload["response"] == "Hello! I'm here to help you."
    assert payload["agent_used"] == agent_key
    assert payload["conversation_id"]

    # Heartbeat should be recorded on the agent after a successful chat
    agents_after = client.get("/api/v1/agents").json()["items"]
    default_agent = next(a for a in agents_after if a["name"] == agent_key)
    assert default_agent.get("last_seen_at") is not None


@patch(
    "app.infrastructure.providers.openai.runtime.OpenAIAgentRuntime.run",
    new_callable=AsyncMock,
)
def test_chat_with_agent_includes_output_schema(
    mock_run: AsyncMock, client: TestClient
) -> None:
    mock_run.return_value = AgentRunResult(
        final_output={"foo": "bar"},
        structured_output={"foo": "bar"},
        response_id="resp-structured",
        usage=None,
        metadata=None,
    )

    schema_key = schema_agent_key()
    chat_request = {"message": "Give me structured", "agent_type": schema_key}

    response = client.post("/api/v1/chat", json=chat_request)
    assert response.status_code == 200

    payload = response.json()
    assert payload["structured_output"] == {"foo": "bar"}
    expected_schema = expected_output_schema(schema_key)
    assert payload["output_schema"] == expected_schema


@patch(
    "app.infrastructure.providers.openai.runtime.OpenAIAgentRuntime.run",
    new_callable=AsyncMock,
)
def test_chat_handoff_uses_final_agent_schema(
    mock_run: AsyncMock, client: TestClient
) -> None:
    schema_key = schema_agent_key()
    mock_run.return_value = AgentRunResult(
        final_output={"foo": "bar"},
        structured_output={"foo": "bar"},
        response_id="resp-structured",
        usage=None,
        metadata=None,
        final_agent=schema_key,
    )

    chat_request = {
        "message": "Route then structure",
        "agent_type": default_agent_key(),
    }

    response = client.post("/api/v1/chat", json=chat_request)
    assert response.status_code == 200

    payload = response.json()
    assert payload["agent_used"] == schema_key
    expected_schema = expected_output_schema(schema_key)
    assert payload["output_schema"] == expected_schema


@patch(
    "app.infrastructure.providers.openai.runtime.OpenAIAgentRuntime.run",
    new_callable=AsyncMock,
)
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
    assert payload["agent_used"] == default_agent_key()


def test_chat_requires_write_scope(client: TestClient) -> None:
    def _read_only_user() -> dict[str, Any]:
        return make_user_payload(scope="conversations:read")

    with override_current_user(app, _read_only_user):
        response = client.post("/api/v1/chat", json={"message": "hi"})
        assert response.status_code == 403


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

    async def _fake_chat(self, _request, *, actor):
        return AgentChatResponse(
            response="ok",
            conversation_id="rate-test",
            agent_used=default_agent_key(),
        )

    monkeypatch.setattr("app.services.agents.service.AgentService.chat", _fake_chat)

    first = client.post("/api/v1/chat", json={"message": "hi"})
    assert first.status_code == 200

    second = client.post("/api/v1/chat", json={"message": "still hi"})
    assert second.status_code == 429
    assert "Rate limit exceeded" in second.text


def test_chat_blocks_when_usage_guardrail_hits(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
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
        assert payload["error"] == "usage_limit_exceeded"
        assert payload["details"]["feature_key"] == "messages"
    finally:
        container.usage_policy_service = previous_service


def test_chat_missing_tenant_claim_rejected(client: TestClient) -> None:
    def _missing_tenant_user() -> dict[str, Any]:
        return make_user_payload(tenant_id=None, scope="conversations:write")

    with override_current_user(app, _missing_tenant_user):
        response = client.post("/api/v1/chat", json={"message": "hi"})
        assert response.status_code == 401
