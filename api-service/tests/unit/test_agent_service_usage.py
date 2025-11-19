from __future__ import annotations

from types import MethodType, SimpleNamespace
from typing import cast

import pytest
from agents.usage import Usage

from app.api.v1.chat.schemas import AgentChatRequest
from app.services.agent_service import AgentRegistry, AgentService, ConversationActorContext
from app.services.conversation_service import ConversationService
from app.services.usage_recorder import UsageEntry, UsageRecorder


class StubUsageRecorder:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[UsageEntry]]] = []

    async def record_batch(self, tenant_id: str, entries: list[UsageEntry]) -> None:
        self.calls.append((tenant_id, entries))


class FakeConversationService:
    def __init__(self) -> None:
        self.repository = None

    def set_repository(self, repo):  # pragma: no cover - unused in tests
        self.repository = repo

    async def append_message(self, *args, **kwargs):  # pragma: no cover - noop
        return None

    async def get_session_state(self, *args, **kwargs):
        return None

    async def update_session_state(self, *args, **kwargs):  # pragma: no cover - noop
        return None


class FakeAgentRegistry:
    def __init__(self):
        self._agent = SimpleNamespace(model="gpt-5.1")

    def get_agent(self, _name):
        return self._agent

    def list_agents(self):  # pragma: no cover - not used
        return ["triage"]


@pytest.mark.asyncio
async def test_chat_records_usage(monkeypatch):
    recorder = StubUsageRecorder()
    service = AgentService(
        conversation_service=cast(ConversationService, FakeConversationService()),
        usage_recorder=cast(UsageRecorder, recorder),
    )
    service._agent_registry = cast(AgentRegistry, FakeAgentRegistry())

    async def fake_run(agent, agent_input, **kwargs):
        usage = Usage(requests=1, input_tokens=123, output_tokens=45, total_tokens=168)
        return SimpleNamespace(
            final_output="ok",
            context_wrapper=SimpleNamespace(usage=usage),
            last_response_id="resp-sync",
        )

    monkeypatch.setattr("app.services.agent_service.agent_runner.run", fake_run)

    actor = ConversationActorContext(tenant_id="tenant-123", user_id="user" )
    request = AgentChatRequest(message="hello")

    response = await service.chat(request, actor=actor)

    assert response.response == "ok"
    assert len(recorder.calls) == 1
    tenant_id, entries = recorder.calls[0]
    assert tenant_id == "tenant-123"
    feature_keys = {entry.feature_key for entry in entries}
    assert feature_keys == {"messages", "input_tokens", "output_tokens"}


class _StreamStub:
    def __init__(self):
        usage = Usage(requests=1, input_tokens=10, output_tokens=5, total_tokens=15)
        self.context_wrapper = SimpleNamespace(usage=usage)
        self.last_response_id = "resp-stream"

    async def stream_events(self):
        if False:  # pragma: no cover - ensures async generator type
            yield None
        return


@pytest.mark.asyncio
async def test_chat_stream_records_usage(monkeypatch):
    recorder = StubUsageRecorder()
    service = AgentService(
        conversation_service=cast(ConversationService, FakeConversationService()),
        usage_recorder=cast(UsageRecorder, recorder),
    )
    service._agent_registry = cast(AgentRegistry, FakeAgentRegistry())

    def fake_stream(agent, agent_input, **kwargs):
        return _StreamStub()

    monkeypatch.setattr("app.services.agent_service.agent_runner.run_streamed", fake_stream)

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

    async for _ in service.chat_stream(request, actor=actor):
        pass

    assert len(sync_calls) == 1
    assert len(calls) == 1
    assert calls[0]["tenant_id"] == "tenant-stream"
