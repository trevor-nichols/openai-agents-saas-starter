from __future__ import annotations

from types import MethodType
from typing import cast

import pytest

from app.api.v1.chat.schemas import AgentChatRequest
from app.domain.ai import AgentDescriptor, AgentRunResult, AgentRunUsage, AgentStreamEvent
from app.domain.ai.ports import AgentStreamingHandle
from app.services.agent_service import AgentService, ConversationActorContext
from app.services.agents.provider_registry import AgentProviderRegistry
from app.services.conversation_service import ConversationService
from app.services.containers import ContainerService
from app.services.usage_recorder import UsageEntry, UsageRecorder


class StubUsageRecorder:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[UsageEntry]]] = []

    async def record_batch(self, tenant_id: str, entries: list[UsageEntry]) -> None:
        self.calls.append((tenant_id, entries))


class FakeConversationService:
    def __init__(self) -> None:
        self.repository = None
        self.usage_calls: list[tuple[str, str, object]] = []

    def set_repository(self, repo):  # pragma: no cover - unused in tests
        self.repository = repo

    async def append_message(self, *args, **kwargs):  # pragma: no cover - noop
        return None

    async def get_session_state(self, *args, **kwargs):
        return None

    async def update_session_state(self, *args, **kwargs):  # pragma: no cover - noop
        return None

    async def record_conversation_created(self, *args, **kwargs):  # pragma: no cover - noop
        return None

    async def persist_run_usage(self, conversation_id, *, tenant_id, usage):
        self.usage_calls.append((conversation_id, tenant_id, usage))

    async def list_run_usage(self, *args, **kwargs):  # pragma: no cover - unused
        return []


class FakeContainerService:
    async def list_agent_bindings(self, *args, **kwargs):  # pragma: no cover - noop
        return {}


class FakeSessionStore:
    def build(self, session_id: str) -> str:  # pragma: no cover - unused in assertions
        return f"session:{session_id}"


class FakeStreamingHandle(AgentStreamingHandle):
    def __init__(self):
        self._events = [
            AgentStreamEvent(kind="lifecycle", event="agent_start", agent="triage"),
            AgentStreamEvent(
                kind="raw_response_event",
                raw_type="response.output_text.delta",
                text_delta="chunk",
            ),
            AgentStreamEvent(
                kind="raw_response_event",
                raw_type="response.completed",
                is_terminal=True,
            ),
        ]
        self._usage = AgentRunUsage(input_tokens=10, output_tokens=5)
        self._last_response_id = "resp-stream"

    async def events(self):
        for event in self._events:
            yield event

    @property
    def usage(self) -> AgentRunUsage:
        return self._usage

    @property
    def last_response_id(self) -> str | None:
        return self._last_response_id


class FakeRuntime:
    def __init__(self, result: AgentRunResult, stream_handle: AgentStreamingHandle):
        self._result = result
        self._stream_handle = stream_handle

    async def run(self, *args, **kwargs) -> AgentRunResult:
        return self._result

    def run_stream(self, *args, **kwargs) -> AgentStreamingHandle:
        return self._stream_handle


class FakeProvider:
    name = "fake"

    def __init__(self, runtime: FakeRuntime):
        self._descriptor = AgentDescriptor(
            key="triage",
            display_name="Triage",
            description="",
            model="gpt-5.1",
        )
        self._runtime = runtime
        self._session_store = FakeSessionStore()

    @property
    def runtime(self) -> FakeRuntime:
        return self._runtime

    @property
    def session_store(self) -> FakeSessionStore:
        return self._session_store

    def list_agents(self):  # pragma: no cover - not used
        return [self._descriptor]

    def resolve_agent(self, preferred_key: str | None = None) -> AgentDescriptor:
        return self._descriptor

    def get_agent(self, agent_key: str) -> AgentDescriptor | None:
        return self._descriptor if agent_key == self._descriptor.key else None

    def default_agent_key(self) -> str:
        return self._descriptor.key

    def tool_overview(self) -> dict[str, list[str]]:  # pragma: no cover - not used
        return {"tool_names": []}

    def mark_seen(self, agent_key: str, ts):  # pragma: no cover - simple stub
        self._descriptor.last_seen_at = ts


@pytest.mark.asyncio
async def test_chat_records_usage():
    recorder = StubUsageRecorder()
    run_result = AgentRunResult(
        final_output="ok",
        response_id="resp-sync",
        usage=AgentRunUsage(input_tokens=123, output_tokens=45),
        metadata={"model": "gpt-5.1"},
    )
    runtime = FakeRuntime(run_result, FakeStreamingHandle())
    provider = FakeProvider(runtime)
    registry = AgentProviderRegistry()
    registry.register(provider, set_default=True)
    service = AgentService(
        conversation_service=cast(ConversationService, FakeConversationService()),
        usage_recorder=cast(UsageRecorder, recorder),
        provider_registry=registry,
        container_service=cast(ContainerService, FakeContainerService()),
    )

    actor = ConversationActorContext(tenant_id="tenant-123", user_id="user" )
    request = AgentChatRequest(message="hello")

    response = await service.chat(request, actor=actor)

    assert response.response == "ok"
    assert len(recorder.calls) == 1
    tenant_id, entries = recorder.calls[0]
    assert tenant_id == "tenant-123"
    feature_keys = {entry.feature_key for entry in entries}
    assert feature_keys == {"messages", "input_tokens", "output_tokens"}


@pytest.mark.asyncio
async def test_chat_stream_records_usage():
    recorder = StubUsageRecorder()
    run_result = AgentRunResult(
        final_output="streamed",
        response_id="resp-stream",
        usage=AgentRunUsage(input_tokens=5, output_tokens=5),
    )
    runtime = FakeRuntime(run_result, FakeStreamingHandle())
    provider = FakeProvider(runtime)
    registry = AgentProviderRegistry()
    registry.register(provider, set_default=True)
    service = AgentService(
        conversation_service=cast(ConversationService, FakeConversationService()),
        usage_recorder=cast(UsageRecorder, recorder),
        provider_registry=registry,
        container_service=cast(ContainerService, FakeContainerService()),
    )

    calls: list[dict[str, object]] = []

    async def fake_record_usage(self, **kwargs):
        calls.append(kwargs)

    service._record_usage_metrics = MethodType(fake_record_usage, service)

    sync_calls: list[bool] = []

    async def fake_sync(self, *args, **kwargs):
        sync_calls.append(True)

    service._sync_session_state = MethodType(fake_sync, service)

    actor = ConversationActorContext(tenant_id="tenant-stream", user_id="user")
    request = AgentChatRequest(message="hello stream")

    yielded = []

    async for evt in service.chat_stream(request, actor=actor):
        yielded.append(evt)

    assert len(sync_calls) == 1
    assert len(calls) == 1
    assert calls[0]["tenant_id"] == "tenant-stream"
    # lifecycle + two raw_response events
    kinds = [e.kind for e in yielded]
    assert "lifecycle" in kinds
