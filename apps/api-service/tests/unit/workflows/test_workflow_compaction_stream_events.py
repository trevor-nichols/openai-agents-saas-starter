from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from app.domain.ai.models import AgentStreamEvent
from app.services.workflows.runner import WorkflowRunner
from app.workflows._shared.specs import WorkflowSpec, WorkflowStep


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
                    "tool_call_id": "call-456",
                    "name": "weather",
                    "content": "sunny",
                },
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
            key="triage", model="gpt", status="active", memory_strategy_defaults=None
        )

    def resolve_agent(self, preferred_key=None):
        return self._descriptor

    def tool_overview(self):
        return {"tool_names": []}

    def mark_seen(self, *_args, **_kwargs):  # pragma: no cover
        return None


class _ProviderRegistry:
    def __init__(self, provider):
        self._provider = provider

    def get_default(self):
        return self._provider


@pytest.mark.asyncio
async def test_workflow_stream_emits_compaction_event():
    provider = _FakeProvider()
    registry = _ProviderRegistry(provider)

    async def _build_ctx(**_kwargs):
        return {}

    async def _noop(*_args, **_kwargs):
        return None

    async def _conversation_exists(*_args, **_kwargs):
        return False

    interaction_builder = SimpleNamespace(build=_build_ctx)
    conversation_service = SimpleNamespace(
        append_message=_noop,
        record_conversation_created=_noop,
        conversation_exists=_conversation_exists,
        update_session_state=_noop,
        get_session_state=_noop,
        get_memory_config=_noop,
    )
    recorder = SimpleNamespace(start=_noop, end=_noop, record_step=_noop)

    async def _ingest_session_items(**kwargs):
        return None

    event_projector = SimpleNamespace(ingest_session_items=_ingest_session_items)

    spec = WorkflowSpec(
        key="wf1",
        display_name="wf1",
        description="test wf",
        steps=(WorkflowStep(agent_key="triage"),),
    )

    runner = WorkflowRunner(
        registry=SimpleNamespace(get=lambda key: spec),
        provider_registry=registry,
        interaction_builder=interaction_builder,
        run_repository=None,
        conversation_service=conversation_service,
        event_projector=event_projector,
    )

    events = []
    async for ev in runner.run_stream(
        spec,
        actor=SimpleNamespace(tenant_id="t1", user_id="u1"),
        message="hi",
        attachments=None,
        conversation_id="conv-1",
    ):
        events.append(ev)

    compaction_events = [ev for ev in events if ev.event == "memory_compaction"]
    assert compaction_events, "expected memory_compaction event in workflow stream"
