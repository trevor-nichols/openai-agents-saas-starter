import asyncio
import types
from dataclasses import dataclass

import pytest

from app.services.agents.policy import AgentRuntimePolicy
from app.services.agents.session_manager import SessionManager
from app.services.conversation_service import ConversationService
from app.domain.conversations import ConversationSessionState


@dataclass
class DummyActor:
    tenant_id: str
    user_id: str


class FakeProvider:
    def __init__(self):
        self.session_store = types.SimpleNamespace(build=lambda sid: f"session:{sid}")
        self.conversation_factory_calls = []
        self.conversation_factory = types.SimpleNamespace(create=self._create)

    async def _create(self, tenant_id, user_id, conversation_key):
        self.conversation_factory_calls.append((tenant_id, user_id, conversation_key))
        await asyncio.sleep(0)
        return f"conv_{conversation_key}"


class FakeConversationService(ConversationService):
    def __init__(self, state: ConversationSessionState | None = None):
        super().__init__()
        self._state = state

    async def get_session_state(self, conversation_id: str, *, tenant_id: str):
        return self._state

    async def update_session_state(self, conversation_id: str, *, tenant_id: str, state):
        self.updated = (conversation_id, tenant_id, state)


@pytest.mark.asyncio
async def test_resolve_provider_conversation_id_uses_existing_valid():
    svc = SessionManager(FakeConversationService(), AgentRuntimePolicy())
    provider = FakeProvider()
    actor = DummyActor(tenant_id="t1", user_id="u1")
    state = ConversationSessionState(provider="openai", provider_conversation_id="conv_abc", sdk_session_id=None)

    cid = await svc.resolve_provider_conversation_id(
        provider=provider,
        actor=actor,
        conversation_id="abc",
        existing_state=state,
    )

    assert cid == "conv_abc"
    assert provider.conversation_factory_calls == []


@pytest.mark.asyncio
async def test_resolve_provider_conversation_id_creates_when_missing():
    svc = SessionManager(FakeConversationService(), AgentRuntimePolicy())
    provider = FakeProvider()
    actor = DummyActor(tenant_id="t1", user_id="u1")

    cid = await svc.resolve_provider_conversation_id(
        provider=provider,
        actor=actor,
        conversation_id="abc",
        existing_state=None,
    )

    assert cid == "conv_abc"
    assert provider.conversation_factory_calls == [("t1", "u1", "abc")]


@pytest.mark.asyncio
async def test_resolve_provider_conversation_id_respects_disable_policy():
    svc = SessionManager(
        FakeConversationService(),
        AgentRuntimePolicy(disable_provider_conversation_creation=True),
    )
    provider = FakeProvider()
    actor = DummyActor(tenant_id="t1", user_id="u1")

    cid = await svc.resolve_provider_conversation_id(
        provider=provider,
        actor=actor,
        conversation_id="abc",
        existing_state=None,
    )

    assert cid is None
    assert provider.conversation_factory_calls == []


@pytest.mark.asyncio
async def test_acquire_session_prefers_provider_when_rebind_policy():
    conv_state = ConversationSessionState(
        provider="openai", provider_conversation_id="conv_existing", sdk_session_id="sdk-123"
    )
    svc = SessionManager(
        FakeConversationService(state=conv_state),
        AgentRuntimePolicy(force_provider_session_rebind=True),
    )
    provider = FakeProvider()

    session_id, handle = await svc.acquire_session(
        provider, tenant_id="t1", conversation_id="abc", provider_conversation_id="conv_new"
    )

    assert session_id == "conv_new"
    assert handle == "session:conv_new"


@pytest.mark.asyncio
async def test_acquire_session_uses_existing_sdk_session():
    conv_state = ConversationSessionState(
        provider="openai", provider_conversation_id="conv_existing", sdk_session_id="sdk-123"
    )
    svc = SessionManager(
        FakeConversationService(state=conv_state),
        AgentRuntimePolicy(force_provider_session_rebind=False),
    )
    provider = FakeProvider()

    session_id, handle = await svc.acquire_session(
        provider, tenant_id="t1", conversation_id="abc", provider_conversation_id=None
    )

    assert session_id == "sdk-123"
    assert handle == "session:sdk-123"


@pytest.mark.asyncio
async def test_sync_session_state_updates_repository():
    conv_service = FakeConversationService()
    svc = SessionManager(conv_service, AgentRuntimePolicy())

    await svc.sync_session_state(
        tenant_id="t1",
        conversation_id="abc",
        session_id="sid",
        provider_name="openai",
        provider_conversation_id="conv_abc",
    )

    conv_id, tenant_id, state = conv_service.updated
    assert conv_id == "abc"
    assert tenant_id == "t1"
    assert state.sdk_session_id == "sid"
    assert state.provider == "openai"
    assert state.provider_conversation_id == "conv_abc"
    assert state.last_session_sync_at is not None
