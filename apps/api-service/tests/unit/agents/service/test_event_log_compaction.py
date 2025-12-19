from __future__ import annotations

from app.services.agents.event_log import EventProjector


class _FakeConversationService:
    def __init__(self):
        self.appended = []

    async def append_run_events(self, conversation_id, *, tenant_id, events):
        self.appended.append((conversation_id, tenant_id, events))


async def test_event_log_preserves_run_item_type():
    svc = _FakeConversationService()
    projector = EventProjector(svc)

    event = {
        "run_item_type": "memory_compaction",
        "payload": {"compacted_count": 1},
        "agent": "triage",
    }

    await projector.ingest_session_items(
        conversation_id="c1",
        tenant_id="t1",
        session_items=[event],
        agent="triage",
        model=None,
        response_id="r1",
    )

    assert svc.appended, "events should be appended"
    _, _, events = svc.appended[0]
    assert events[0].run_item_type == "memory_compaction"


async def test_event_log_does_not_assign_tool_call_id_for_reasoning_items():
    svc = _FakeConversationService()
    projector = EventProjector(svc)

    event = {
        "type": "reasoning",
        "id": "rs_123",
        "delta": "thinking...",
        "agent": "triage",
    }

    await projector.ingest_session_items(
        conversation_id="c2",
        tenant_id="t2",
        session_items=[event],
        agent="triage",
        model=None,
        response_id="r2",
    )

    _, _, events = svc.appended[0]
    assert events[0].run_item_type == "reasoning"
    assert events[0].tool_call_id is None
    assert events[0].tool_name is None


async def test_event_log_assigns_tool_call_id_for_tool_call_items():
    svc = _FakeConversationService()
    projector = EventProjector(svc)

    event = {
        "type": "tool_call",
        "id": "ws_456",
        "name": "web_search",
        "arguments": {"query": "hello"},
        "agent": "triage",
    }

    await projector.ingest_session_items(
        conversation_id="c3",
        tenant_id="t3",
        session_items=[event],
        agent="triage",
        model=None,
        response_id="r3",
    )

    _, _, events = svc.appended[0]
    assert events[0].run_item_type == "tool_call"
    assert events[0].tool_call_id == "ws_456"
    assert events[0].tool_name == "web_search"


async def test_event_log_classifies_web_search_call_as_tool_call():
    svc = _FakeConversationService()
    projector = EventProjector(svc)

    event = {
        "type": "web_search_call",
        "id": "ws_999",
        "status": "completed",
        "action": {"type": "search", "query": "hello"},
        "agent": "triage",
    }

    await projector.ingest_session_items(
        conversation_id="c4",
        tenant_id="t4",
        session_items=[event],
        agent="triage",
        model=None,
        response_id="r4",
    )

    _, _, events = svc.appended[0]
    assert events[0].run_item_type == "tool_call"
    assert events[0].tool_call_id == "ws_999"
    assert events[0].tool_name == "web_search"
    assert events[0].call_arguments == {"type": "search", "query": "hello"}
