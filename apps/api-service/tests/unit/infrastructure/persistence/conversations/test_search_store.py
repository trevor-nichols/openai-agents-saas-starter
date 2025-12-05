"""Tests for ConversationSearchStore using SQLite fallback strategy."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import AsyncGenerator
from uuid import UUID

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.persistence.conversations.message_store import ConversationMessageStore
from app.infrastructure.persistence.conversations.search_store import ConversationSearchStore
from app.infrastructure.persistence.conversations.models import AgentConversation, AgentMessage
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


@pytest.mark.asyncio
async def test_search_returns_hits(session_factory: async_sessionmaker[AsyncSession]) -> None:
    search = ConversationSearchStore(session_factory)
    # Seed a conversation and a message containing the query term
    async with session_factory() as session:
        conv = AgentConversation(
            id=UUID("6a9c9c72-34a5-4c3f-9d43-5f5c91164e14"),
            conversation_key="conv-1",
            tenant_id=UUID("e1f329f8-433d-4d44-a5a3-5d4fd0c6fb9c"),
            agent_entrypoint="triage",
            message_count=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        msg = AgentMessage(
            conversation_id=conv.id,
            position=0,
            role="assistant",
            content={"text": "Searchable content foobar"},
            created_at=datetime.now(UTC),
        )
        session.add_all([conv, msg])
        await session.commit()

    page = await search.search_conversations(
        tenant_id="e1f329f8-433d-4d44-a5a3-5d4fd0c6fb9c",
        query="foobar",
        limit=5,
    )
    assert page.next_cursor is None
    assert len(page.items) == 1
    hit = page.items[0]
    assert hit.record.conversation_id == "conv-1"
    assert hit.record.messages[0].content.startswith("Searchable content")


@pytest.mark.asyncio
async def test_search_paginates_with_cursor(session_factory: async_sessionmaker[AsyncSession]) -> None:
    search = ConversationSearchStore(session_factory)
    async with session_factory() as session:
        base_ts = datetime.now(UTC)
        items = []
        for i in range(3):
            conv = AgentConversation(
                id=UUID(int=1000 + i),
                conversation_key=f"conv-{i}",
                tenant_id=UUID("e1f329f8-433d-4d44-a5a3-5d4fd0c6fb9c"),
                agent_entrypoint="triage",
                updated_at=base_ts,
                created_at=base_ts,
                message_count=1,
            )
            msg = AgentMessage(
                conversation_id=conv.id,
                position=0,
                role="assistant",
                content={"text": f"shared term number {i}"},
                created_at=base_ts,
            )
            items.extend([conv, msg])
        session.add_all(items)
        await session.commit()

    first_page = await search.search_conversations(
        tenant_id="e1f329f8-433d-4d44-a5a3-5d4fd0c6fb9c", query="term", limit=2
    )
    assert len(first_page.items) == 2
    assert first_page.next_cursor is not None

    second_page = await search.search_conversations(
        tenant_id="e1f329f8-433d-4d44-a5a3-5d4fd0c6fb9c",
        query="term",
        limit=2,
        cursor=first_page.next_cursor,
    )
    assert len(second_page.items) == 1
    assert second_page.next_cursor is None
