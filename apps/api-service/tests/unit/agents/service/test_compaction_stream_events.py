from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import cast
from typing import Any

import pytest

from app.api.v1.chat.schemas import AgentChatRequest, MemoryStrategyRequest
from app.domain.ai.models import AgentStreamEvent
from app.services.agents import AgentService
from app.services.agents.policy import AgentRuntimePolicy
from app.services.conversation_service import ConversationService


class _FakeBaseSession:
    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []

    async def get_items(self, limit=None):
        return list(self.items if limit is None else self.items[:limit])

    async def add_items(self, items):
        self.items.extend(items)

    async def clear_session(self):
        self.items.clear()

    async def pop_item(self):  # pragma: no cover
        if self.items:
            return self.items.pop()
        return None


class _FakeSessionStore:
    def build(self, session_id: str):
        return _FakeBaseSession()


class _FakeStreamHandle:
    def __init__(self, session_handle):
        self._session_handle = session_handle
        self.last_response_id = "resp-1"

    async def events(self):
        # Simulate provider writing items that trigger compaction
        yield AgentStreamEvent(
            kind="lifecycle",
            event="memory_compaction",
            run_item_type="memory_compaction",
            agent="triage",
            payload={"compacted_count": 1},
        )
        await self._session_handle.add_items(
            [
                {"role": "user", "content": "hi", "type": "message"},
                {
                    "role": "assistant",
                    "type": "tool_output",
                    "tool_call_id": "call-123",
                    "name": "weather",
                    "content": "rainy",
                },
                {"role": "user", "content": "bye", "type": "message"},
            ]
        )
        yield AgentStreamEvent(kind="run_item_stream_event", agent="triage")


class _FakeRuntime:
    def run_stream(self, *_args, **kwargs):
        session = kwargs.get("session")
        return _FakeStreamHandle(session)


class _FakeProvider:
    def __init__(self):
        self.name = "openai"
        self.session_store = _FakeSessionStore()
        self.runtime = _FakeRuntime()
        self._descriptor = SimpleNamespace(
            key="triage",
            model="gpt",
            status="active",
            memory_strategy_defaults=None,
            output_schema=None,
        )

    def resolve_agent(self, preferred_key=None):
        return self._descriptor

    def tool_overview(self):
        return {"tool_names": []}

    def mark_seen(self, *_args, **_kwargs):
        return None


class _ProviderRegistry:
    def __init__(self, provider):
        self._provider = provider

    def get_default(self):
        return self._provider


@pytest.mark.asyncio
async def test_chat_stream_emits_compaction_event():
    provider = _FakeProvider()
    registry = _ProviderRegistry(provider)

    async def _build_ctx(**_kwargs):
        return {}

    async def _noop(*_args, **_kwargs):
        return None

    async def _acquire_session(*args, **kwargs):
        return ("sess-1", provider.session_store.build("sess-1"))

    interaction_builder = SimpleNamespace(build=_build_ctx)
    conversation_service = SimpleNamespace(
        append_message=_noop,
        record_conversation_created=_noop,
        get_session_state=_noop,
        update_session_state=_noop,
        get_memory_config=_noop,
        persist_summary=_noop,
    )
    session_manager = SimpleNamespace(
        acquire_session=_acquire_session,
        sync_session_state=_noop,
    )
    event_projector_calls: list[list[dict[str, Any]]] = []

    async def _ingest_session_items(**kwargs):
        event_projector_calls.append(kwargs.get("session_items", []))

    event_projector = SimpleNamespace(ingest_session_items=_ingest_session_items)

    async def _record_usage(*_args, **_kwargs):
        return None

    async def _ingest_images(*_args, **_kwargs):
        return []
    agent_service = AgentService(
        provider_registry=registry,
        interaction_builder=interaction_builder,
        conversation_service=cast(ConversationService, conversation_service),
        session_manager=session_manager,
        usage_service=SimpleNamespace(record=_record_usage),
        usage_recorder=None,
        attachment_service=SimpleNamespace(
            ingest_image_outputs=_ingest_images,
            to_attachment_payload=lambda *args, **kwargs: {},
            to_attachment_schema=lambda *args, **kwargs: {},
            attachment_metadata_note=lambda *args, **kwargs: {},
        ),
        event_projector=event_projector,
        policy=AgentRuntimePolicy(),
    )

    request = AgentChatRequest(
        message="hi",
        memory_strategy=MemoryStrategyRequest(mode="compact", compact_trigger_turns=1, compact_keep=1),
    )
    actor = SimpleNamespace(tenant_id="t1", user_id="u1")

    events = []
    async for ev in agent_service.chat_stream(request, actor=actor):
        events.append(ev)

    compaction_events = [ev for ev in events if ev.event == "memory_compaction"]
    assert compaction_events, "expected memory_compaction event in stream"
    payload = compaction_events[0].payload or {}
    assert payload.get("compacted_count") == 1

    # Persistence path should include the compaction mapping
    flattened = [m for call in event_projector_calls for m in call]
    assert event_projector_calls, "compaction event should be projected to event log"
