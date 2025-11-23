"""Integration tests for conversation search in Postgres repository."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.domain.conversations import ConversationMessage, ConversationMetadata
from app.infrastructure.persistence.conversations.postgres import (
    PostgresConversationRepository,
)

from .test_postgres_migrations import _seed_tenant

pytestmark = pytest.mark.postgres


async def _seed_message(
    repo: PostgresConversationRepository,
    *,
    tenant_id: str,
    conversation_id: str,
    text: str,
    minutes_ago: int,
) -> None:
    ts = datetime.now(UTC) - timedelta(minutes=minutes_ago)
    await repo.add_message(
        conversation_id,
        ConversationMessage(role="user", content=text, timestamp=ts),
        tenant_id=tenant_id,
        metadata=ConversationMetadata(tenant_id=tenant_id, agent_entrypoint="triage"),
    )


@pytest.mark.asyncio
async def test_search_prioritizes_rank_over_recency(migrated_engine: AsyncEngine) -> None:
    """Higher text relevance outranks more recent but weaker matches."""

    session_factory = async_sessionmaker(migrated_engine, expire_on_commit=False)
    repo = PostgresConversationRepository(session_factory)
    tenant_id = await _seed_tenant(session_factory)

    await _seed_message(repo, tenant_id=tenant_id, conversation_id="high-rank", text="alpha alpha beta", minutes_ago=10)
    await _seed_message(repo, tenant_id=tenant_id, conversation_id="recent-low", text="alpha gamma", minutes_ago=1)
    await _seed_message(repo, tenant_id=tenant_id, conversation_id="middle", text="alpha", minutes_ago=5)

    page = await repo.search_conversations(tenant_id=tenant_id, query="alpha", limit=2)

    ids = [hit.record.conversation_id for hit in page.items]
    assert ids == ["high-rank", "recent-low"], "rank should outrank recency when query matches more strongly"
    assert page.next_cursor is not None, "cursor should be present when more results remain"

    # Scores are available on Postgres; ensure the top hit scored at least as high as the second.
    assert page.items[0].score is not None
    assert page.items[1].score is not None
    assert page.items[0].score >= page.items[1].score


@pytest.mark.asyncio
async def test_search_cursor_paginates_results(migrated_engine: AsyncEngine) -> None:
    """Cursor should return the next page ordered by rank then recency."""

    session_factory = async_sessionmaker(migrated_engine, expire_on_commit=False)
    repo = PostgresConversationRepository(session_factory)
    tenant_id = await _seed_tenant(session_factory)

    await _seed_message(repo, tenant_id=tenant_id, conversation_id="conv-1", text="alpha", minutes_ago=3)
    await _seed_message(repo, tenant_id=tenant_id, conversation_id="conv-2", text="alpha", minutes_ago=2)
    await _seed_message(repo, tenant_id=tenant_id, conversation_id="conv-3", text="alpha", minutes_ago=1)

    first_page = await repo.search_conversations(tenant_id=tenant_id, query="alpha", limit=2)
    assert len(first_page.items) == 2
    assert first_page.next_cursor is not None

    second_page = await repo.search_conversations(
        tenant_id=tenant_id,
        query="alpha",
        limit=2,
        cursor=first_page.next_cursor,
    )

    remaining_ids = [hit.record.conversation_id for hit in second_page.items]
    assert remaining_ids == ["conv-1"], "cursor should advance to the next set of ranked results"
    assert second_page.next_cursor is None
