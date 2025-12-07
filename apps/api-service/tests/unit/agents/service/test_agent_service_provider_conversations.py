from __future__ import annotations

from typing import cast

import pytest

from app.api.v1.chat.schemas import AgentChatRequest
from app.domain.ai import AgentDescriptor, AgentRunResult
from app.domain.conversations import ConversationSessionState
from app.services.agent_service import AgentService, ConversationActorContext
from app.services.agents.policy import AgentRuntimePolicy
from app.services.agents.provider_registry import AgentProviderRegistry
from app.services.conversation_service import ConversationService
from app.services.containers import ContainerService


class FakeConversationService(ConversationService):
    def __init__(self):
        super().__init__(repository=None)
        self.messages: list[dict] = []
        self.session_states: dict[tuple[str, str], ConversationSessionState] = {}

    async def append_message(self, conversation_id, message, *, tenant_id, metadata):
        self.messages.append(
            {
                "conversation_id": conversation_id,
                "tenant_id": tenant_id,
                "metadata": metadata,
                "message": message,
            }
        )

    async def get_session_state(
        self, conversation_id, *, tenant_id
    ) -> ConversationSessionState | None:
        return self.session_states.get((tenant_id, conversation_id))

    async def update_session_state(
        self, conversation_id, *, tenant_id, state: ConversationSessionState
    ):
        self.session_states[(tenant_id, conversation_id)] = state

    async def record_conversation_created(  # pragma: no cover - stub to satisfy AgentService
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        agent_entrypoint: str | None = None,
        existed: bool | None = None,
    ) -> None:
        return None

    async def conversation_exists(self, conversation_id: str, *, tenant_id: str) -> bool:
        return False

    async def persist_run_usage(self, conversation_id, *, tenant_id, usage):  # pragma: no cover
        return None

    async def list_run_usage(self, *args, **kwargs):  # pragma: no cover
        return []


class FakeContainerService:
    async def list_agent_bindings(self, *args, **kwargs):  # pragma: no cover - noop
        return {}


class CapturingSessionStore:
    def __init__(self):
        self.last_session_id: str | None = None

    def build(self, session_id: str):
        self.last_session_id = session_id
        return f"session:{session_id}"


class CapturingRuntime:
    def __init__(self):
        self.calls: list[str | None] = []

    async def run(
        self, agent_key, message, *, session=None, conversation_id=None, metadata=None, options=None
    ):
        self.calls.append(conversation_id)
        return AgentRunResult(final_output="ok", response_id="resp", usage=None, metadata={})

    def run_stream(self, *args, **kwargs):  # pragma: no cover - not used here
        raise NotImplementedError


class FakeProvider:
    name = "openai"

    def __init__(self, runtime: CapturingRuntime, conversation_id: str | None):
        self._descriptor = AgentDescriptor(
            key="triage", display_name="Triage", description="", model="gpt-5.1"
        )
        self._runtime = runtime
        self._session_store = CapturingSessionStore()
        self._conversation_id = conversation_id

    @property
    def runtime(self):
        return self._runtime

    @property
    def session_store(self):
        return self._session_store

    @property
    def conversation_factory(self):
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

    async def create(self, *, tenant_id, user_id, conversation_key):
        return self._conversation_id

    def mark_seen(self, agent_key, ts):  # pragma: no cover - simple stub
        self._descriptor.last_seen_at = ts


@pytest.mark.asyncio
async def test_agent_service_uses_conv_id_when_available(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DISABLE_PROVIDER_CONVERSATION_CREATION", "false")
    runtime = CapturingRuntime()
    provider = FakeProvider(runtime, conversation_id="conv_abc123")
    registry = AgentProviderRegistry()
    registry.register(provider, set_default=True)
    conv_service = FakeConversationService()
    service = AgentService(
        conversation_service=conv_service,
        provider_registry=registry,
        container_service=cast(ContainerService, FakeContainerService()),
        policy=AgentRuntimePolicy(disable_provider_conversation_creation=False),
    )

    actor = ConversationActorContext(tenant_id="tenant-1", user_id="user-1")
    request = AgentChatRequest(message="hello", conversation_id="local-uuid")

    await service.chat(request, actor=actor)

    # Provider conversation ids are intentionally not propagated (we rely on SDK session only)
    assert runtime.calls == ["local-uuid"]
    assert provider.session_store.last_session_id == "local-uuid"
    state = conv_service.session_states[("tenant-1", "local-uuid")]
    assert state.provider_conversation_id is None
    # Provider name is retained even when we skip provider conversation ids
    assert state.provider == "openai"


@pytest.mark.asyncio
async def test_agent_service_ignores_non_conv_ids(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DISABLE_PROVIDER_CONVERSATION_CREATION", "false")
    runtime = CapturingRuntime()
    provider = FakeProvider(runtime, conversation_id="not-a-conv-id")
    registry = AgentProviderRegistry()
    registry.register(provider, set_default=True)
    conv_service = FakeConversationService()
    service = AgentService(
        conversation_service=conv_service,
        provider_registry=registry,
        container_service=cast(ContainerService, FakeContainerService()),
        policy=AgentRuntimePolicy(disable_provider_conversation_creation=False),
    )

    actor = ConversationActorContext(tenant_id="tenant-1", user_id="user-1")
    request = AgentChatRequest(message="hello", conversation_id="local-uuid")

    await service.chat(request, actor=actor)

    # falls back to local conversation id because provider ID was invalid
    assert runtime.calls == ["local-uuid"]
    assert provider.session_store.last_session_id == "local-uuid"
    state = conv_service.session_states[("tenant-1", "local-uuid")]
    assert state.provider_conversation_id is None
