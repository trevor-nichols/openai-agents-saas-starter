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
