"""Contract tests for streaming chat endpoints."""

from __future__ import annotations

import json
from typing import Any, Callable, cast
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from tests.utils.contract_auth import make_user_payload, override_current_user
from tests.utils.contract_env import configure_contract_env

configure_contract_env()

pytestmark = pytest.mark.auto_migrations(enabled=True)

from app.api.v1.shared.streaming import FinalEvent, PublicSseEvent  # noqa: E402
from app.bootstrap.container import get_container  # noqa: E402
from app.core import settings as config_module  # noqa: E402
from app.domain.ai import AgentStreamEvent  # noqa: E402
from app.infrastructure.db.engine import get_engine, init_engine  # noqa: E402
from app.infrastructure.providers.openai import build_openai_provider  # noqa: E402
from app.services.agents.provider_registry import get_provider_registry  # noqa: E402
from app.services.conversation_service import conversation_service  # noqa: E402
from main import app  # noqa: E402
from tests.utils.agent_contract import (  # noqa: E402
    default_agent_key,
    schema_agent_key,
)
from tests.utils.stream_assertions import assert_common_stream  # noqa: E402


def _stub_current_user() -> dict[str, Any]:
    return make_user_payload()


class _FakeStreamingHandle:
    """Minimal AgentStreamingHandle for contract tests."""

    def __init__(self, events: list[AgentStreamEvent]) -> None:
        self._events = events
        self.last_response_id = events[-1].response_id if events else None
        self.metadata: dict[str, Any] = {}

    async def events(self):
        for ev in self._events:
            yield ev


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


@pytest.fixture
def guardrail_provider_factory() -> Callable[[Any, Any | None], Any]:
    """Return a factory that registers a guardrail-enabled provider and refreshes AgentService."""

    def _register(engine: Any, pipeline: Any | None = None) -> Any:
        registry = get_provider_registry()
        registry.clear()
        from app.guardrails._shared.loaders import initialize_guardrails

        initialize_guardrails()
        pipeline_source = pipeline or {"version": 1}
        provider = build_openai_provider(
            settings_factory=config_module.get_settings,
            conversation_searcher=lambda tenant_id, query: conversation_service.search(
                tenant_id=tenant_id, query=query
            ),
            engine=engine,
            auto_create_tables=True,
            enable_guardrail_bundles=True,
            guardrail_pipeline_source=pipeline_source,
        )
        registry.register(provider, set_default=True)
        container = get_container()
        container.agent_service = None
        return provider

    return _register


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
            line = (
                raw_obj.decode()
                if isinstance(raw_obj, (bytes, bytearray))
                else cast(str, raw_obj)
            )
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
            line = (
                raw_obj.decode()
                if isinstance(raw_obj, (bytes, bytearray))
                else cast(str, raw_obj)
            )
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
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    guardrail_provider_factory,
) -> None:
    engine = get_engine()
    assert engine is not None
    guardrail_provider_factory(engine)

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

    monkeypatch.setattr("app.services.agents.service.AgentService.chat_stream", _fake_chat_stream)

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
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    guardrail_provider_factory,
) -> None:
    engine = get_engine()
    assert engine is not None
    guardrail_provider_factory(engine)

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

    monkeypatch.setattr("app.services.agents.service.AgentService.chat_stream", _fake_chat_stream)

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
