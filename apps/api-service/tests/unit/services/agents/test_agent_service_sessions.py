from __future__ import annotations

import pytest

from app.api.v1.chat.schemas import AgentChatRequest
from app.domain.ai import AgentDescriptor, AgentStreamEvent
from app.services.agent_service import AgentService
from app.services.agents.context import ConversationActorContext


class _StubConversationService:
    def __init__(self):
        self.states: dict[str, object] = {}

    def set_repository(self, repo):  # pragma: no cover - compatibility hook
        return None

    async def get_session_state(self, conversation_id: str, *, tenant_id: str):
        return self.states.get(conversation_id)

    async def append_message(self, *args, **kwargs):
        return None

    async def update_session_state(self, conversation_id: str, *, tenant_id: str, state):
        self.states[conversation_id] = state


class _StubAttachmentService:
    async def ingest_image_outputs(self, *args, **kwargs):
        return []

    def to_attachment_payload(self, att):
        return att

    def to_attachment_schema(self, att):
        return att

    def attachment_metadata_note(self, attachments):
        return {}


class _StubUsageService:
    async def record(self, *args, **kwargs):
        return None


class _StubEventProjector:
    async def ingest_session_items(self, *args, **kwargs):
        return None


class _StubSessionStore:
    def build(self, session_id: str):
        return f"session:{session_id}"


class _DummyStreamHandle:
    def __init__(self):
        self.last_response_id = None
        self.usage = None

    async def events(self):
        yield AgentStreamEvent(
            kind="run_item_stream_event",
            is_terminal=True,
            conversation_id=None,
            response_id=None,
            sequence_number=None,
            raw_type=None,
            run_item_name=None,
            run_item_type=None,
            tool_call_id=None,
            tool_name=None,
            agent=None,
            new_agent=None,
            text_delta=None,
            reasoning_delta=None,
            event=None,
            payload=None,
            attachments=None,
            metadata=None,
            structured_output=None,
            response_text="ok",
        )


class _StubRuntime:
    def __init__(self):
        self.calls: list[dict] = []

    def run_stream(
        self,
        agent_key: str,
        message: str,
        *,
        session=None,
        conversation_id=None,
        metadata=None,
        options=None,
    ):
        self.calls.append(
            {
                "agent_key": agent_key,
                "message": message,
                "session": session,
                "conversation_id": conversation_id,
                "metadata": metadata,
                "options": options,
            }
        )
        return _DummyStreamHandle()


class _StubProvider:
    name = "openai"

    def __init__(self, runtime: _StubRuntime):
        self.runtime = runtime
        self.session_store = _StubSessionStore()

    def resolve_agent(self, preferred_key: str | None):
        key = preferred_key or "triage"
        return AgentDescriptor(
            key=key,
            display_name=key,
            description="",
            model="gpt",
            capabilities=(),
        )

    def tool_overview(self):
        return {}


class _StubRegistry:
    def __init__(self, provider: _StubProvider):
        self._provider = provider

    def get_default(self):
        return self._provider


@pytest.mark.asyncio
async def test_stream_uses_session_without_provider_conversation_id():
    runtime = _StubRuntime()
    provider = _StubProvider(runtime)
    registry = _StubRegistry(provider)
    conversation_service = _StubConversationService()

    svc = AgentService(
        conversation_service=conversation_service,
        provider_registry=registry,
    )
    # Replace heavy collaborators with stubs
    svc._attachment_service = _StubAttachmentService()
    svc._usage_service = _StubUsageService()
    svc._event_projector = _StubEventProjector()

    request = AgentChatRequest(message="hi", agent_type="triage")
    actor = ConversationActorContext(tenant_id="tenant-1", user_id="user-1")

    # Execute stream (drain generator)
    async for _ in svc.chat_stream(request, actor=actor):
        pass

    assert runtime.calls, "runtime.run_stream should be invoked"
    call = runtime.calls[0]
    assert call["conversation_id"] is None, "conversation_id must be omitted when session is used"
    assert call["session"] is not None, "session handle should be provided"
