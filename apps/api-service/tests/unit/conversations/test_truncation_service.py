"""Unit tests for per-message deletion (conversation truncation)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import AsyncGenerator
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.conversations import (
    ConversationMessageNotDeletableError,
    ConversationMessageNotFoundError,
)
from app.infrastructure.persistence.conversations import ids as ids_helpers
from app.infrastructure.persistence.conversations.ledger_models import (
    ConversationLedgerEvent,
    ConversationLedgerSegment,
)
from app.infrastructure.persistence.conversations.ledger_query_store import ConversationLedgerQueryStore
from app.infrastructure.persistence.conversations.message_store import ConversationMessageStore
from app.infrastructure.persistence.conversations.models import AgentConversation, AgentMessage
from app.infrastructure.persistence.conversations.search_store import ConversationSearchStore
from app.infrastructure.persistence.models.base import Base
from app.services.conversations.truncation_service import ConversationTruncationService


@pytest_asyncio.fixture()
async def session_factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()


async def _seed_conversation(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    tenant_id: UUID,
    actor_user_id: str,
) -> tuple[str, str]:
    """Seed one conversation with one segment, messages, and ledger events.

    Returns:
      conversation_id, delete_message_id
    """

    conversation_id = "conv-1"
    conversation_uuid = ids_helpers.coerce_conversation_uuid(conversation_id)
    conversation_key = ids_helpers.derive_conversation_key(conversation_id)

    base_ts = datetime.now(UTC) - timedelta(minutes=5)
    delete_msg_created = base_ts + timedelta(seconds=40)

    async with session_factory() as session:
        segment_id = uuid4()
        segment = ConversationLedgerSegment(
            id=segment_id,
            tenant_id=tenant_id,
            conversation_id=conversation_uuid,
            segment_index=0,
            created_at=base_ts,
            updated_at=base_ts,
        )

        conversation = AgentConversation(
            id=conversation_uuid,
            conversation_key=conversation_key,
            tenant_id=tenant_id,
            user_id=UUID(actor_user_id),
            agent_entrypoint="triage",
            message_count=6,
            created_at=base_ts,
            updated_at=base_ts,
        )

        delete_message_id = 105
        messages = [
            AgentMessage(
                id=101,
                conversation_id=conversation_uuid,
                segment_id=segment_id,
                position=0,
                role="user",
                content={"text": "hello"},
                created_at=base_ts + timedelta(seconds=0),
            ),
            AgentMessage(
                id=102,
                conversation_id=conversation_uuid,
                segment_id=segment_id,
                position=1,
                role="assistant",
                content={"text": "hi"},
                created_at=base_ts + timedelta(seconds=10),
            ),
            AgentMessage(
                id=103,
                conversation_id=conversation_uuid,
                segment_id=segment_id,
                position=2,
                role="user",
                content={"text": "question"},
                created_at=base_ts + timedelta(seconds=20),
            ),
            AgentMessage(
                id=104,
                conversation_id=conversation_uuid,
                segment_id=segment_id,
                position=3,
                role="assistant",
                content={"text": "answer"},
                created_at=base_ts + timedelta(seconds=30),
            ),
            AgentMessage(
                id=delete_message_id,
                conversation_id=conversation_uuid,
                segment_id=segment_id,
                position=4,
                role="user",
                content={"text": "delete me"},
                created_at=delete_msg_created,
            ),
            AgentMessage(
                id=106,
                conversation_id=conversation_uuid,
                segment_id=segment_id,
                position=5,
                role="assistant",
                content={"text": "later"},
                created_at=base_ts + timedelta(seconds=50),
            ),
        ]

        event_before = ConversationLedgerEvent(
            tenant_id=tenant_id,
            conversation_id=conversation_uuid,
            segment_id=segment_id,
            schema_version="public_sse_v1",
            kind="message.delta",
            stream_id="stream-1",
            event_id=1,
            server_timestamp=base_ts + timedelta(seconds=35),
            payload_size_bytes=10,
            payload_json={"schema": "public_sse_v1", "kind": "message.delta"},
        )
        event_after = ConversationLedgerEvent(
            tenant_id=tenant_id,
            conversation_id=conversation_uuid,
            segment_id=segment_id,
            schema_version="public_sse_v1",
            kind="message.delta",
            stream_id="stream-2",
            event_id=1,
            server_timestamp=base_ts + timedelta(seconds=45),
            payload_size_bytes=10,
            payload_json={"schema": "public_sse_v1", "kind": "message.delta"},
        )

        session.add_all([conversation, segment, *messages, event_before, event_after])
        await session.commit()

        # Ensure ledger event ids are assigned so later assertions can compare.
        await session.refresh(event_before)
        await session.refresh(event_after)

    return conversation_id, str(delete_message_id)


@pytest.mark.asyncio
async def test_truncate_hides_messages_and_ledger_events(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id = UUID("e1f329f8-433d-4d44-a5a3-5d4fd0c6fb9c")
    actor_user_id = str(UUID("6a9c9c72-34a5-4c3f-9d43-5f5c91164e14"))

    conversation_id, delete_message_id = await _seed_conversation(
        session_factory,
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
    )

    svc = ConversationTruncationService(session_factory)
    await svc.truncate_from_user_message(
        conversation_id,
        tenant_id=str(tenant_id),
        actor_user_id=actor_user_id,
        message_id=delete_message_id,
    )

    store = ConversationMessageStore(session_factory)
    visible = await store.get_messages(conversation_id, tenant_id=str(tenant_id))
    assert [m.content for m in visible] == ["hello", "hi", "question", "answer"]
    assert all(m.message_id is not None for m in visible)

    ledger = ConversationLedgerQueryStore(session_factory)
    events, cursor = await ledger.list_events_page(
        conversation_id,
        tenant_id=str(tenant_id),
        limit=10,
        cursor=None,
    )
    assert cursor is None
    assert len(events) == 1

    # Truncated content should no longer appear in search results.
    search = ConversationSearchStore(session_factory)
    page = await search.search_conversations(
        tenant_id=str(tenant_id),
        query="later",
        limit=10,
    )
    assert page.items == []


@pytest.mark.asyncio
async def test_truncate_rejects_non_user_messages(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id = UUID("e1f329f8-433d-4d44-a5a3-5d4fd0c6fb9c")
    actor_user_id = str(UUID("6a9c9c72-34a5-4c3f-9d43-5f5c91164e14"))
    conversation_id, _ = await _seed_conversation(
        session_factory,
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
    )

    svc = ConversationTruncationService(session_factory)
    with pytest.raises(ConversationMessageNotDeletableError):
        await svc.truncate_from_user_message(
            conversation_id,
            tenant_id=str(tenant_id),
            actor_user_id=actor_user_id,
            message_id="104",  # assistant message
        )


@pytest.mark.asyncio
async def test_truncate_raises_for_missing_message(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id = UUID("e1f329f8-433d-4d44-a5a3-5d4fd0c6fb9c")
    actor_user_id = str(UUID("6a9c9c72-34a5-4c3f-9d43-5f5c91164e14"))
    conversation_id, _ = await _seed_conversation(
        session_factory,
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
    )

    svc = ConversationTruncationService(session_factory)
    with pytest.raises(ConversationMessageNotFoundError):
        await svc.truncate_from_user_message(
            conversation_id,
            tenant_id=str(tenant_id),
            actor_user_id=actor_user_id,
            message_id="9999",
        )
