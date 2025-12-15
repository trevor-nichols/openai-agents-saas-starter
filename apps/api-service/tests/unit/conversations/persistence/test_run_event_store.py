"""Tests for run-event persistence store."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import AsyncGenerator
from uuid import UUID

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.conversations import ConversationEvent, ConversationNotFoundError
from app.infrastructure.persistence.conversations.run_event_store import RunEventStore
from app.infrastructure.persistence.conversations.models import AgentConversation
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


async def _insert_conversation(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    conv_id: str,
    tenant_id: str,
    message_count: int = 0,
) -> None:
    async with session_factory() as session:
        conv = AgentConversation(
            id=UUID(conv_id),
            conversation_key="conv-1",
            tenant_id=UUID(tenant_id),
            agent_entrypoint="triage",
            message_count=message_count,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        session.add(conv)
        await session.commit()


@pytest.mark.asyncio
async def test_add_and_get_run_events(session_factory: async_sessionmaker[AsyncSession]) -> None:
    store = RunEventStore(session_factory)
    conv_id = "6a9c9c72-34a5-4c3f-9d43-5f5c91164e14"
    tenant_id = "e1f329f8-433d-4d44-a5a3-5d4fd0c6fb9c"

    await _insert_conversation(session_factory, conv_id=conv_id, tenant_id=tenant_id, message_count=2)

    events = [
        ConversationEvent(
            run_item_type="message",
            run_item_name="reply",
            role="assistant",
            agent="triage",
            content_text="hello",
            response_id="resp-1",
            sequence_no=None,
            timestamp=datetime.now(UTC),
        ),
        # duplicate response_id should be ignored
        ConversationEvent(
            run_item_type="message",
            run_item_name="reply",
            role="assistant",
            agent="triage",
            content_text="hello again",
            response_id="resp-1",
            sequence_no=None,
            timestamp=datetime.now(UTC),
        ),
        ConversationEvent(
            run_item_type="tool_call",
            run_item_name="search",
            role="assistant",
            agent="triage",
            tool_name="search",
            sequence_no=None,
            timestamp=datetime.now(UTC),
        ),
    ]

    await store.add_run_events(conv_id, tenant_id=tenant_id, events=events)
    stored = await store.get_run_events(conv_id, tenant_id=tenant_id)

    assert len(stored) == 2  # duplicate response id filtered
    assert stored[0].sequence_no == 0
    assert stored[1].sequence_no == 1
    assert stored[0].content_text == "hello"
    assert stored[1].tool_name == "search"


@pytest.mark.asyncio
async def test_get_run_events_raises_for_missing_conversation(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    store = RunEventStore(session_factory)
    conv_id = "7c4f0d64-1e6c-4f8f-9cd3-0b2f6a1f4480"
    tenant_id = "2d22d29e-81f0-4b3c-bd38-7cb2a3f7b2a1"

    with pytest.raises(ConversationNotFoundError):
        await store.get_run_events(conv_id, tenant_id=tenant_id)


@pytest.mark.asyncio
async def test_get_run_events_returns_empty_for_existing_conversation(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    store = RunEventStore(session_factory)
    conv_id = "c2d5c6e7-9b16-4e78-9c8a-3f6b8c9f1f0d"
    tenant_id = "0d7b1b4e-52ab-4e0c-9b1a-2c4f5a6b7c8d"

    await _insert_conversation(session_factory, conv_id=conv_id, tenant_id=tenant_id, message_count=0)

    events = await store.get_run_events(conv_id, tenant_id=tenant_id)
    assert events == []
