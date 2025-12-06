"""Tests for ConversationMessageStore message pagination."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import AsyncGenerator
from uuid import UUID

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.conversations import ConversationNotFoundError
from app.infrastructure.persistence.conversations.message_store import ConversationMessageStore
from app.infrastructure.persistence.conversations.models import AgentConversation, AgentMessage
from app.infrastructure.persistence.conversations import ids as ids_helpers
from app.infrastructure.persistence.models.base import Base


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


def _seed_conversation(session: AsyncSession, *, tenant_id: UUID) -> None:
    base_ts = datetime.now(UTC) - timedelta(minutes=5)
    conv_uuid = ids_helpers.coerce_conversation_uuid("conv-1")
    conv_key = ids_helpers.derive_conversation_key("conv-1")
    conversation = AgentConversation(
        id=conv_uuid,
        conversation_key=conv_key,
        tenant_id=tenant_id,
        agent_entrypoint="triage",
        message_count=3,
        created_at=base_ts,
        updated_at=base_ts,
    )
    messages = [
        AgentMessage(
            id=i + 1,
            conversation_id=conv_uuid,
            position=i,
            role="assistant",
            content={"text": f"msg-{i}"},
            created_at=base_ts + timedelta(seconds=i),
        )
        for i in range(3)
    ]
    session.add(conversation)
    session.add_all(messages)


@pytest.mark.asyncio
async def test_paginate_messages_desc(session_factory: async_sessionmaker[AsyncSession]) -> None:
    store = ConversationMessageStore(session_factory)
    tenant_id = UUID("e1f329f8-433d-4d44-a5a3-5d4fd0c6fb9c")
    async with session_factory() as session:
        _seed_conversation(session, tenant_id=tenant_id)
        await session.commit()

    first_page = await store.paginate_messages(
        conversation_id="conv-1",
        tenant_id=str(tenant_id),
        limit=2,
        cursor=None,
        direction="desc",
    )

    assert [m.content for m in first_page.items] == ["msg-2", "msg-1"]
    assert first_page.next_cursor is not None

    second_page = await store.paginate_messages(
        conversation_id="conv-1",
        tenant_id=str(tenant_id),
        limit=2,
        cursor=first_page.next_cursor,
        direction="desc",
    )

    assert [m.content for m in second_page.items] == ["msg-0"]
    assert second_page.next_cursor is None


@pytest.mark.asyncio
async def test_paginate_messages_asc(session_factory: async_sessionmaker[AsyncSession]) -> None:
    store = ConversationMessageStore(session_factory)
    tenant_id = UUID("e1f329f8-433d-4d44-a5a3-5d4fd0c6fb9c")
    async with session_factory() as session:
        _seed_conversation(session, tenant_id=tenant_id)
        await session.commit()

    first_page = await store.paginate_messages(
        conversation_id="conv-1",
        tenant_id=str(tenant_id),
        limit=2,
        cursor=None,
        direction="asc",
    )

    assert [m.content for m in first_page.items] == ["msg-0", "msg-1"]
    assert first_page.next_cursor is not None

    second_page = await store.paginate_messages(
        conversation_id="conv-1",
        tenant_id=str(tenant_id),
        limit=2,
        cursor=first_page.next_cursor,
        direction="asc",
    )

    assert [m.content for m in second_page.items] == ["msg-2"]
    assert second_page.next_cursor is None


@pytest.mark.asyncio
async def test_paginate_messages_wrong_tenant_raises(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    store = ConversationMessageStore(session_factory)
    tenant_id = UUID("e1f329f8-433d-4d44-a5a3-5d4fd0c6fb9c")
    async with session_factory() as session:
        _seed_conversation(session, tenant_id=tenant_id)
        await session.commit()

    with pytest.raises(ConversationNotFoundError):
        await store.paginate_messages(
            conversation_id="conv-1",
            tenant_id=str(UUID(int=999)),
            limit=1,
        )
