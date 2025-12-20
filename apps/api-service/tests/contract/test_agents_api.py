"""Test suite covering agent-facing endpoints and services."""

import json
import os
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("RATE_LIMIT_REDIS_URL", os.environ["REDIS_URL"])
os.environ.setdefault("AUTH_CACHE_REDIS_URL", os.environ["REDIS_URL"])
os.environ.setdefault("SECURITY_TOKEN_REDIS_URL", os.environ["REDIS_URL"])
os.environ.setdefault("ENABLE_BILLING", "false")
os.environ.setdefault("ENABLE_USAGE_GUARDRAILS", "false")

pytestmark = pytest.mark.auto_migrations(enabled=True)

from app.infrastructure.db.engine import init_engine  # noqa: E402


@pytest_asyncio.fixture(autouse=True)
async def _ensure_engine_initialized():
    """Guarantee the async engine/session factory is ready for each test."""

    await init_engine(run_migrations=True)

from app.api.dependencies import usage as usage_dependencies  # noqa: E402
from app.api.dependencies.auth import require_current_user  # noqa: E402
from app.api.v1.chat import router as chat_router  # noqa: E402
from app.api.v1.chat.schemas import AgentChatResponse  # noqa: E402
from app.api.v1.shared.streaming import FinalEvent, PublicSseEvent  # noqa: E402
from app.bootstrap.container import get_container  # noqa: E402
from app.core import settings as config_module  # noqa: E402
from app.domain.ai import AgentRunResult, AgentStreamEvent  # noqa: E402
from app.domain.conversations import ConversationMessage, ConversationMetadata  # noqa: E402
from tests.utils.stream_assertions import assert_common_stream  # noqa: E402
from tests.utils.agent_contract import (  # noqa: E402
    default_agent_key,
    expected_output_schema,
    expected_tooling_flags_by_agent,
    expected_tools_by_agent,
    schema_agent_key,
    spec_index,
)
from app.services.conversation_service import conversation_service  # noqa: E402
from app.guardrails._shared.events import emit_guardrail_event  # noqa: E402
from app.guardrails._shared.specs import GuardrailCheckResult  # noqa: E402
from app.infrastructure.providers.openai import build_openai_provider  # noqa: E402
from app.services.agent_service import agent_service  # noqa: E402
from app.services.agents.provider_registry import get_provider_registry  # noqa: E402
from app.services.shared.rate_limit_service import RateLimitExceeded, rate_limiter  # noqa: E402
from app.services.usage_policy_service import (  # noqa: E402
    UsagePolicyDecision,
    UsagePolicyResult,
    UsagePolicyService,
    UsageViolation,
)
from main import app  # noqa: E402

TEST_TENANT_ID = str(uuid4())


class _FakeStreamingHandle:
    """Minimal AgentStreamingHandle for contract tests."""

    def __init__(self, events: list[AgentStreamEvent]) -> None:
        self._events = events
        self.last_response_id = events[-1].response_id if events else None
        self.metadata: dict[str, Any] = {}

    async def events(self):
        for ev in self._events:
            yield ev


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
    assert "items" in payload
    assert isinstance(payload["items"], list)
    assert payload["total"] >= len(payload["items"])
    items = payload["items"]
    specs = spec_index()
    assert all(agent["name"] in specs for agent in items)
    assert any(agent["name"] == default_agent_key() for agent in items)
    expected_tooling = expected_tooling_flags_by_agent()
    for agent in items:
        if agent.get("output_schema") is not None:
            assert isinstance(agent["output_schema"], dict)
        tooling = agent.get("tooling")
        assert isinstance(tooling, dict)
        assert tooling == expected_tooling[agent["name"]]


def test_list_available_agents_pagination(client: TestClient) -> None:
    first = client.get("/api/v1/agents?limit=2")
    assert first.status_code == 200
    first_payload = first.json()

    assert len(first_payload["items"]) <= 2
    assert first_payload["total"] >= len(first_payload["items"])

    next_cursor = first_payload.get("next_cursor")
    if first_payload["total"] > len(first_payload["items"]):
        assert next_cursor is not None
        second = client.get(f"/api/v1/agents?cursor={next_cursor}&limit=2")
        assert second.status_code == 200
        second_payload = second.json()
        assert len(second_payload["items"]) <= 2
        # Ensure we advanced the cursor
        assert set(a["name"] for a in second_payload["items"]).isdisjoint(
            set(a["name"] for a in first_payload["items"])
        )
    else:
        assert next_cursor is None


def test_list_available_agents_invalid_cursor(client: TestClient) -> None:
    response = client.get("/api/v1/agents?cursor=not-a-cursor")
    assert response.status_code == 400


def test_list_available_agents_invalid_limit(client: TestClient) -> None:
    response = client.get("/api/v1/agents?limit=0")
    assert response.status_code == 422  # validation rejects at FastAPI layer


def test_get_agent_status(client: TestClient) -> None:
    agent_key = default_agent_key()
    response = client.get(f"/api/v1/agents/{agent_key}/status")
    assert response.status_code == 200

    payload = response.json()
    assert payload["name"] == agent_key
    assert payload["status"] == "active"
    assert "output_schema" in payload
    expected_tooling = expected_tooling_flags_by_agent()
    assert payload["tooling"] == expected_tooling[agent_key]


def test_get_nonexistent_agent_status(client: TestClient) -> None:
    response = client.get("/api/v1/agents/nonexistent/status")
    assert response.status_code == 404


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


def test_tools_endpoint_returns_per_agent_tooling(client: TestClient) -> None:
    response = client.get("/api/v1/tools")
    assert response.status_code == 200

    payload = response.json()
    assert "per_agent" in payload
    per_agent = payload["per_agent"]
    expected = expected_tools_by_agent()
    assert expected.keys() <= per_agent.keys()
    for agent, tools in expected.items():
        assert set(per_agent[agent]) == tools


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


@patch("app.infrastructure.providers.openai.runtime.OpenAIAgentRuntime.run_stream")
def test_chat_stream_persists_assistant_message(mock_run_stream, client: TestClient) -> None:
    schema_key = schema_agent_key()
    mock_events = [
        AgentStreamEvent(
            kind="run_item_stream_event",
            response_id="resp_stream",
            response_text="Hello world",
            is_terminal=True,
        )
    ]
    mock_run_stream.return_value = _FakeStreamingHandle(mock_events)

    payload = {"message": "Hi there", "agent_type": schema_key}
    with client.stream("POST", "/api/v1/chat/stream", json=payload) as response:
        assert response.status_code == 200
        lines = []
        for raw in response.iter_lines():
            if not raw:
                continue
            if isinstance(raw, (bytes, bytearray)):
                line = raw.decode()
            else:
                line = raw
            if not line.startswith("data: "):
                continue
            data = json.loads(line[len("data: ") :])
            lines.append(data)

    assert lines, "stream returned no events"
    events = [PublicSseEvent.model_validate(line).root for line in lines]
    assert_common_stream(events)
    terminal = events[-1]
    assert isinstance(terminal, FinalEvent)
    conversation_id = terminal.conversation_id
    assert conversation_id

    history_response = client.get(f"/api/v1/conversations/{conversation_id}")
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history["messages"]) >= 2
    assert any(msg["role"] == "assistant" for msg in history["messages"])


@patch("app.infrastructure.providers.openai.runtime.OpenAIAgentRuntime.run_stream")
def test_chat_stream_handoff_updates_schema(mock_run_stream, client: TestClient) -> None:
    schema_key = schema_agent_key()
    mock_events = [
        AgentStreamEvent(
            kind="agent_updated_stream_event",
            new_agent=schema_key,
            response_id="resp_stream_handoff",
        ),
        AgentStreamEvent(
            kind="run_item_stream_event",
            response_id="resp_stream_handoff",
            structured_output={"foo": "bar"},
            is_terminal=True,
        ),
    ]
    mock_run_stream.return_value = _FakeStreamingHandle(mock_events)

    payload = {"message": "handoff me", "agent_type": default_agent_key()}
    with client.stream("POST", "/api/v1/chat/stream", json=payload) as response:
        assert response.status_code == 200
        lines = []
        for raw in response.iter_lines():
            if not raw:
                continue
            raw_obj: Any = raw
            line = raw_obj.decode() if isinstance(raw_obj, (bytes, bytearray)) else cast(str, raw_obj)
            if not line.startswith("data: "):
                continue
            lines.append(json.loads(line[len("data: ") :]))

    assert lines, "stream returned no events"
    events = [PublicSseEvent.model_validate(line).root for line in lines]
    assert_common_stream(events)
    terminal = events[-1]
    assert isinstance(terminal, FinalEvent)
    assert terminal.final.structured_output == {"foo": "bar"}


@patch("app.infrastructure.providers.openai.runtime.OpenAIAgentRuntime.run_stream")
def test_chat_stream_handoff_final_output_keeps_schema(
    mock_run_stream, client: TestClient
) -> None:
    schema_key = schema_agent_key()
    mock_events = [
        AgentStreamEvent(
            kind="agent_updated_stream_event",
            new_agent=schema_key,
            response_id="resp_stream_handoff_final",
        ),
        AgentStreamEvent(
            kind="run_item_stream_event",
            response_id="resp_stream_handoff_final",
            structured_output={"foo": "bar"},
            is_terminal=True,
        ),
    ]
    mock_run_stream.return_value = _FakeStreamingHandle(mock_events)

    payload = {"message": "handoff then finalize", "agent_type": default_agent_key()}
    with client.stream("POST", "/api/v1/chat/stream", json=payload) as response:
        assert response.status_code == 200
        lines = []
        for raw in response.iter_lines():
            if not raw:
                continue
            raw_obj: Any = raw
            line = raw_obj.decode() if isinstance(raw_obj, (bytes, bytearray)) else cast(str, raw_obj)
            if not line.startswith("data: "):
                continue
            lines.append(json.loads(line[len("data: ") :]))

    assert lines, "stream returned no events"
    events = [PublicSseEvent.model_validate(line).root for line in lines]
    assert_common_stream(events)
    terminal = events[-1]
    assert isinstance(terminal, FinalEvent)
    assert terminal.final.structured_output == {"foo": "bar"}


def test_chat_stream_does_not_emit_guardrail_events_to_public_stream(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _fake_chat_stream(*args, **kwargs):
        yield AgentStreamEvent(
            kind="guardrail_result",
            response_id="resp-guardrail-pipeline",
            guardrail_stage="input",
            guardrail_key="off_topic_prompts",
            guardrail_name="Off Topic Prompts",
            guardrail_tripwire_triggered=True,
            guardrail_suppressed=False,
            guardrail_flagged=True,
            guardrail_confidence=0.9,
        )
        yield AgentStreamEvent(
            kind="run_item_stream_event",
            response_id="resp-guardrail-pipeline",
            run_item_type="message",
            is_terminal=True,
            payload={"item": {"type": "message"}},
        )

    monkeypatch.setattr("app.services.agent_service.AgentService.chat_stream", _fake_chat_stream)

    payload = {"message": "contains pii: user@example.com", "agent_type": default_agent_key()}
    events = []
    with client.stream("POST", "/api/v1/chat/stream", json=payload) as response:
        assert response.status_code == 200
        for raw in response.iter_lines():
            if not raw:
                continue
            line = raw
            if not line.startswith("data: "):
                continue
            parsed = PublicSseEvent.model_validate_json(line[len("data: ") :]).root
            events.append(parsed)
            if getattr(parsed, "kind", None) in {"final", "error"}:
                break

    assert_common_stream(events)


def test_chat_stream_does_not_emit_tool_guardrail_events_to_public_stream(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _fake_chat_stream(*args, **kwargs):
        yield AgentStreamEvent(
            kind="guardrail_result",
            response_id="resp-tool-guardrail",
            guardrail_stage="tool_input",
            guardrail_key="pii_tool_input",
            guardrail_name="PII Detection (Tool Input)",
            guardrail_tripwire_triggered=True,
            guardrail_suppressed=False,
            guardrail_flagged=True,
            guardrail_confidence=0.9,
            tool_name="search",
            tool_call_id="tool-call-123",
        )
        yield AgentStreamEvent(
            kind="run_item_stream_event",
            response_id="resp-tool-guardrail",
            run_item_type="message",
            is_terminal=True,
            payload={"item": {"type": "message"}},
        )

    monkeypatch.setattr("app.services.agent_service.AgentService.chat_stream", _fake_chat_stream)

    payload = {"message": "trigger tool guardrail", "agent_type": default_agent_key()}
    events = []
    with client.stream("POST", "/api/v1/chat/stream", json=payload) as response:
        assert response.status_code == 200
        for raw in response.iter_lines():
            if not raw:
                continue
            line = raw
            if not line.startswith("data: "):
                continue
            parsed = PublicSseEvent.model_validate_json(line[len("data: ") :]).root
            events.append(parsed)
            if getattr(parsed, "kind", None) in {"final", "error"}:
                break

    assert_common_stream(events)


def _register_guardrail_provider(engine, pipeline) -> None:
    registry = get_provider_registry()
    registry.clear()
    from app.guardrails._shared.loaders import initialize_guardrails

    initialize_guardrails()
    provider = build_openai_provider(
        settings_factory=config_module.get_settings,
        conversation_searcher=lambda tenant_id, query: conversation_service.search(
            tenant_id=tenant_id, query=query
        ),
        engine=engine,
        auto_create_tables=True,
        enable_guardrail_bundles=True,
        guardrail_pipeline_source=pipeline,
    )
    registry.register(provider, set_default=True)
    get_container().agent_service = None


@patch(
    "app.infrastructure.providers.openai.runtime.OpenAIAgentRuntime.run",
    new_callable=AsyncMock,
)
def test_conversation_lifecycle(mock_run: AsyncMock, client: TestClient) -> None:
    mock_run.return_value = AgentRunResult(
        final_output="Sure, let's get started.",
        response_id="resp",
        usage=None,
        metadata=None,
    )

    chat_request = {"message": "Start a new plan", "agent_type": default_agent_key()}
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
    page = agent_service.list_available_agents_page(limit=10, cursor=None, search=None)
    names = {agent.name for agent in page.items}

    expected_names = set(spec_index().keys())
    assert expected_names.issubset(names)
    assert default_agent_key() in names


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

    async def _fake_chat(self, _request, *, actor):
        return AgentChatResponse(
            response="ok",
            conversation_id="rate-test",
            agent_used=default_agent_key(),
        )

    monkeypatch.setattr("app.services.agent_service.AgentService.chat", _fake_chat)

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

@pytest.mark.asyncio
async def test_conversation_repository_roundtrip() -> None:
    repository = agent_service.conversation_repository
    await repository.clear_conversation("integration-test", tenant_id=TEST_TENANT_ID)

    await repository.add_message(
        "integration-test",
        ConversationMessage(role="user", content="Test message"),
        tenant_id=TEST_TENANT_ID,
        metadata=ConversationMetadata(
            tenant_id=TEST_TENANT_ID,
            agent_entrypoint=default_agent_key(),
        ),
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
