from __future__ import annotations

import pytest

from app.api.v1.chat.schemas import AgentChatRequest
from app.domain.ai import AgentDescriptor, AgentRunResult
from app.domain.ai.models import AgentStreamEvent
from app.domain.conversations import ConversationSessionState
from app.services.agents import AgentService, ConversationActorContext
from app.services.agents.policy import AgentRuntimePolicy
from app.services.agents.provider_registry import AgentProviderRegistry
from app.services.conversation_service import ConversationService
from app.services.containers import ContainerService
from app.infrastructure.providers.openai.lifecycle import LifecycleEventBus


class _FakeConversationService(ConversationService):
    def __init__(self):
        super().__init__(repository=None)
        self.messages: list[dict] = []

    async def append_message(self, conversation_id, message, *, tenant_id, metadata):
        self.messages.append(
            {
                "conversation_id": conversation_id,
                "tenant_id": tenant_id,
                "metadata": metadata,
                "message": message,
            }
        )

    async def get_session_state(self, conversation_id, *, tenant_id):
        return None

    async def get_memory_config(self, conversation_id, *, tenant_id):  # pragma: no cover - noop
        return None

    async def update_session_state(self, conversation_id, *, tenant_id, state: ConversationSessionState):
        return None

    async def record_conversation_created(self, *args, **kwargs):  # pragma: no cover - unused
        return None

    async def conversation_exists(self, conversation_id, *, tenant_id) -> bool:
        return False


class _FakeContainerService:
    async def list_agent_bindings(self, *args, **kwargs):  # pragma: no cover - noop
        return {}


class _HandoffRuntime:
    def __init__(self, handoff_count: int, final_agent: str | None):
        self.handoff_count = handoff_count
        self.final_agent = final_agent
        self.stream_handle = None

    async def run(
        self, agent_key, message, *, session=None, conversation_id=None, metadata=None, options=None
    ):
        return AgentRunResult(
            final_output="done",
            response_id="resp",
            usage=None,
            metadata={},
            handoff_count=self.handoff_count,
            final_agent=self.final_agent,
        )

    def run_stream(self, *args, **kwargs):
        if self.stream_handle is None:
            raise RuntimeError("stream_handle not set on _HandoffRuntime")
        return self.stream_handle


class _HandoffProvider:
    name = "openai"

    def __init__(self, runtime: _HandoffRuntime):
        class _SessionStore:
            def build(self, session_id: str):  # pragma: no cover - simple stub
                return f"session:{session_id}"

        self._descriptor = AgentDescriptor(
            key="triage", display_name="Triage", description="", model="gpt-5.1"
        )
        self._runtime = runtime
        self._session_store = _SessionStore()

    @property
    def runtime(self):
        return self._runtime

    @property
    def session_store(self):  # pragma: no cover - trivial stub
        return self._session_store

    @property
    def conversation_factory(self):  # pragma: no cover - not exercised
        return self

    def list_agents(self):
        return [self._descriptor]

    def resolve_agent(self, preferred_key=None):
        return self._descriptor

    def get_agent(self, agent_key):
        return self._descriptor if agent_key == self._descriptor.key else None

    def default_agent_key(self):
        return self._descriptor.key

    def tool_overview(self):  # pragma: no cover - not needed
        return {"tool_names": []}

    async def create(self, *, tenant_id, user_id, conversation_key):  # pragma: no cover
        return None

    def mark_seen(self, agent_key, ts):  # pragma: no cover - stub
        self._descriptor.last_seen_at = ts


@pytest.mark.asyncio
async def test_chat_sets_handoff_flag_and_final_agent():
    runtime = _HandoffRuntime(handoff_count=1, final_agent="Researcher")
    provider = _HandoffProvider(runtime)
    registry = AgentProviderRegistry()
    registry.register(provider, set_default=True)

    conv_service = _FakeConversationService()
    service = AgentService(
        conversation_service=conv_service,
        provider_registry=registry,
        container_service=_FakeContainerService(),
        policy=AgentRuntimePolicy(disable_provider_conversation_creation=True),
    )

    actor = ConversationActorContext(tenant_id="tenant-1", user_id="user-1")
    request = AgentChatRequest(message="hello", conversation_id="conv-1")

    response = await service.chat(request, actor=actor)

    assert response.handoff_occurred is True
    assert response.agent_used == "Researcher"
    # Metadata persisted should include the handoff count
    assert conv_service.messages[-1]["metadata"].handoff_count == 1


class _FakeAttachmentService:
    def __init__(self):
        self.ingest_calls = 0

    async def ingest_image_outputs(self, *args, **kwargs):
        self.ingest_calls += 1
        return []

    async def ingest_container_file_citations(self, *args, **kwargs):
        return []

    def to_attachment_payload(self, attachment):
        return attachment

    def attachment_metadata_note(self, attachments):
        return {}


class _FakeStreamingHandle:
    def __init__(self, events):
        self._events = events
        self.last_response_id = "resp-1"
        self.usage = None

    async def events(self):
        for ev in self._events:
            yield ev


class _FakeStreamingHandleWithBus:
    def __init__(self, events, bus: LifecycleEventBus):
        self._events = events
        self._bus = bus
        self.last_response_id = "resp-2"
        self.usage = None

    async def events(self):
        async for ev in self._bus.drain():
            yield ev
        for ev in self._events:
            yield ev


@pytest.mark.asyncio
async def test_chat_stream_persists_final_agent_and_handoff_count():
    # Prepare stream: agent update -> content -> terminal
    events = [
        AgentStreamEvent(
            kind="agent_updated_stream_event",
            new_agent="Researcher",
            is_terminal=False,
        ),
        AgentStreamEvent(
            kind="run_item_stream_event",
            response_text="hi",
            is_terminal=False,
        ),
        AgentStreamEvent(
            kind="run_item_stream_event",
            is_terminal=True,
        ),
    ]
    runtime = _HandoffRuntime(handoff_count=0, final_agent=None)
    runtime.stream_handle = _FakeStreamingHandle(events)
    provider = _HandoffProvider(runtime)
    registry = AgentProviderRegistry()
    registry.register(provider, set_default=True)

    conv_service = _FakeConversationService()
    attachment_service = _FakeAttachmentService()
    service = AgentService(
        conversation_service=conv_service,
        provider_registry=registry,
        container_service=_FakeContainerService(),
        attachment_service=attachment_service,
        policy=AgentRuntimePolicy(disable_provider_conversation_creation=True),
    )

    actor = ConversationActorContext(tenant_id="tenant-1", user_id="user-1")
    request = AgentChatRequest(message="hello", conversation_id="conv-stream")

    # Exhaust the async generator to trigger persistence
    events_out = []
    async for ev in service.chat_stream(request, actor=actor):
        events_out.append(ev)

    assert any(ev.kind == "agent_updated_stream_event" for ev in events_out)
    # Persistence should have recorded the updated agent and handoff count
    metadata = conv_service.messages[-1]["metadata"]
    assert metadata.active_agent == "Researcher"
    assert metadata.handoff_count == 1


@pytest.mark.asyncio
async def test_chat_stream_counts_handoffs_from_lifecycle_bus():
    bus = LifecycleEventBus()
    await bus.emit(
        AgentStreamEvent(
            kind="lifecycle",
            event="handoff",
            agent="Triage",
            new_agent="Researcher",
            is_terminal=False,
        )
    )
    streamed_events = [
        AgentStreamEvent(
            kind="agent_updated_stream_event",
            new_agent="Researcher",
            is_terminal=False,
        ),
        AgentStreamEvent(
            kind="run_item_stream_event",
            response_text="hi",
            is_terminal=False,
        ),
        AgentStreamEvent(
            kind="run_item_stream_event",
            is_terminal=True,
        ),
    ]
    runtime = _HandoffRuntime(handoff_count=0, final_agent=None)
    runtime.stream_handle = _FakeStreamingHandleWithBus(streamed_events, bus)
    provider = _HandoffProvider(runtime)
    registry = AgentProviderRegistry()
    registry.register(provider, set_default=True)

    conv_service = _FakeConversationService()
    attachment_service = _FakeAttachmentService()
    service = AgentService(
        conversation_service=conv_service,
        provider_registry=registry,
        container_service=_FakeContainerService(),
        attachment_service=attachment_service,
        policy=AgentRuntimePolicy(disable_provider_conversation_creation=True),
    )

    actor = ConversationActorContext(tenant_id="tenant-1", user_id="user-1")
    request = AgentChatRequest(message="hello", conversation_id="conv-stream-bus")

    events_out = []
    async for ev in service.chat_stream(request, actor=actor):
        events_out.append(ev)

    lifecycle_handoffs = [ev for ev in events_out if ev.kind == "lifecycle" and ev.event == "handoff"]
    agent_updates = [ev for ev in events_out if ev.kind == "agent_updated_stream_event"]

    metadata = conv_service.messages[-1]["metadata"]
    assert metadata.active_agent == "Researcher"
    assert metadata.handoff_count == len(agent_updates) == len(lifecycle_handoffs) == 1
