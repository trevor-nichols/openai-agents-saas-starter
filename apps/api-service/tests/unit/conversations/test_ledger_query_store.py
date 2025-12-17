from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from app.bootstrap import get_container
from app.infrastructure.persistence.conversations.ledger_models import (
    ConversationLedgerEvent,
    ConversationLedgerSegment,
)
from app.infrastructure.persistence.conversations.ledger_query_store import (
    ConversationLedgerQueryStore,
)
from app.infrastructure.persistence.conversations.models import AgentConversation, TenantAccount


@pytest.mark.asyncio
async def test_ledger_query_store_filters_truncated_segments() -> None:
    container = get_container()
    assert container.session_factory is not None

    tenant_id = uuid.uuid4()
    conversation_id = uuid.uuid4()

    async with container.session_factory() as session:
        tenant = TenantAccount(id=tenant_id, slug="tenant", name="Tenant")
        conversation = AgentConversation(
            id=conversation_id,
            conversation_key=str(conversation_id),
            tenant_id=tenant_id,
            agent_entrypoint="triage",
        )
        segment0 = ConversationLedgerSegment(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            segment_index=0,
            parent_segment_id=None,
        )
        session.add_all([tenant, conversation, segment0])
        await session.flush()

        def event_payload(kind: str, *, stream_id: str, event_id: int) -> dict[str, object]:
            return {
                "schema": "public_sse_v1",
                "kind": kind,
                "event_id": event_id,
                "stream_id": stream_id,
                "server_timestamp": "2025-12-17T12:00:00.000Z",
                "conversation_id": str(conversation_id),
                "response_id": None,
                "agent": "triage",
            }

        e1 = ConversationLedgerEvent(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            segment_id=segment0.id,
            schema_version="public_sse_v1",
            kind="lifecycle",
            stream_id="stream_0",
            event_id=1,
            server_timestamp=datetime.now(tz=UTC),
            payload_size_bytes=1,
            payload_json=event_payload("lifecycle", stream_id="stream_0", event_id=1),
        )
        e2 = ConversationLedgerEvent(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            segment_id=segment0.id,
            schema_version="public_sse_v1",
            kind="tool.status",
            stream_id="stream_0",
            event_id=2,
            server_timestamp=datetime.now(tz=UTC),
            payload_size_bytes=1,
            payload_json=event_payload("tool.status", stream_id="stream_0", event_id=2),
        )
        e3 = ConversationLedgerEvent(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            segment_id=segment0.id,
            schema_version="public_sse_v1",
            kind="final",
            stream_id="stream_0",
            event_id=3,
            server_timestamp=datetime.now(tz=UTC),
            payload_size_bytes=1,
            payload_json=event_payload("final", stream_id="stream_0", event_id=3),
        )
        session.add_all([e1, e2, e3])
        await session.flush()

        segment0.truncated_at = datetime.now(tz=UTC)
        segment0.visible_through_event_id = e2.id

        segment1 = ConversationLedgerSegment(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            segment_index=1,
            parent_segment_id=segment0.id,
        )
        session.add(segment1)
        await session.flush()

        e4 = ConversationLedgerEvent(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            segment_id=segment1.id,
            schema_version="public_sse_v1",
            kind="lifecycle",
            stream_id="stream_1",
            event_id=1,
            server_timestamp=datetime.now(tz=UTC),
            payload_size_bytes=1,
            payload_json=event_payload("lifecycle", stream_id="stream_1", event_id=1),
        )
        e5 = ConversationLedgerEvent(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            segment_id=segment1.id,
            schema_version="public_sse_v1",
            kind="final",
            stream_id="stream_1",
            event_id=2,
            server_timestamp=datetime.now(tz=UTC),
            payload_size_bytes=1,
            payload_json=event_payload("final", stream_id="stream_1", event_id=2),
        )
        session.add_all([e4, e5])
        await session.commit()

        expected_visible_ids = [e1.id, e2.id, e4.id, e5.id]

    store = ConversationLedgerQueryStore(container.session_factory)
    page, next_cursor = await store.list_events_page(
        str(conversation_id),
        tenant_id=str(tenant_id),
        limit=10,
        cursor=None,
    )
    assert [row.id for row in page] == expected_visible_ids
    assert next_cursor is None

    page1, cursor1 = await store.list_events_page(
        str(conversation_id),
        tenant_id=str(tenant_id),
        limit=2,
        cursor=None,
    )
    assert [row.id for row in page1] == expected_visible_ids[:2]
    assert cursor1 is not None

    page2, cursor2 = await store.list_events_page(
        str(conversation_id),
        tenant_id=str(tenant_id),
        limit=10,
        cursor=cursor1,
    )
    assert [row.id for row in page2] == expected_visible_ids[2:]
    assert cursor2 is None

