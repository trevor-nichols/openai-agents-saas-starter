"""Search-specific persistence for conversations."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any, Protocol, cast

from sqlalchemy import String, and_, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql.elements import ColumnElement

from app.domain.conversations import ConversationSearchHit, ConversationSearchPage
from app.infrastructure.persistence.conversations.cursors import (
    decode_search_cursor,
    encode_search_cursor,
)
from app.infrastructure.persistence.conversations.ids import parse_tenant_id
from app.infrastructure.persistence.conversations.ledger_models import ConversationLedgerSegment
from app.infrastructure.persistence.conversations.mappers import record_from_model
from app.infrastructure.persistence.conversations.models import (
    AgentConversation,
    AgentMessage,
)


class SearchStrategy(Protocol):
    def rank_expression(self, ts_query: ColumnElement[Any]) -> ColumnElement[Any]: ...

    def filter_clause(self, ts_query: ColumnElement[Any]) -> ColumnElement[bool]: ...


class PostgresSearchStrategy:
    def rank_expression(self, ts_query: ColumnElement[Any]) -> ColumnElement[Any]:
        return func.ts_rank_cd(AgentMessage.text_tsv, ts_query)

    def filter_clause(self, ts_query: ColumnElement[Any]) -> ColumnElement[bool]:
        return AgentMessage.text_tsv.op("@@")(ts_query)


class FallbackSearchStrategy:
    """Simple LIKE-based search for SQLite/test envs."""

    def rank_expression(self, ts_query: ColumnElement[Any]) -> ColumnElement[Any]:
        return func.length(AgentMessage.content.cast(String))

    def filter_clause(self, ts_query: ColumnElement[Any]) -> ColumnElement[bool]:
        return func.lower(AgentMessage.content.cast(String)).like(ts_query)


class ConversationSearchStore:
    """Isolated search logic so the repository stays small."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def search_conversations(
        self,
        *,
        tenant_id: str,
        query: str,
        limit: int,
        cursor: str | None = None,
        agent_entrypoint: str | None = None,
    ) -> ConversationSearchPage:
        tenant_uuid = parse_tenant_id(tenant_id)
        limit = max(1, min(limit, 50))
        if not query.strip():
            raise ValueError("Query cannot be empty")

        cursor_rank: float | None = None
        cursor_ts: datetime | None = None
        cursor_uuid: uuid.UUID | None = None
        if cursor:
            cursor_rank, cursor_ts, cursor_uuid = decode_search_cursor(cursor)

        async with self._session_factory() as session:
            dialect = session.bind.dialect.name if session.bind else ""
            ts_query_expr = func.plainto_tsquery("english", query)
            ts_query = cast(ColumnElement[Any], ts_query_expr)
            if dialect == "postgresql":
                strategy: SearchStrategy = PostgresSearchStrategy()
            else:
                strategy = FallbackSearchStrategy()
                ts_query = cast(ColumnElement[Any], literal(f"%{query.lower()}%"))

            base_filters = [AgentConversation.tenant_id == tenant_uuid]
            if agent_entrypoint:
                base_filters.append(AgentConversation.agent_entrypoint == agent_entrypoint)

            rank_expr = strategy.rank_expression(ts_query)
            search_filter = strategy.filter_clause(ts_query)

            base_query = (
                select(
                    AgentConversation.id.label("cid"),
                    AgentConversation.updated_at.label("updated_at"),
                    func.max(rank_expr).label("rank"),
                )
                .join(AgentMessage, AgentMessage.conversation_id == AgentConversation.id)
                .join(
                    ConversationLedgerSegment,
                    ConversationLedgerSegment.id == AgentMessage.segment_id,
                )
                .where(*base_filters, search_filter)
                .where(
                    or_(
                        ConversationLedgerSegment.truncated_at.is_(None),
                        and_(
                            ConversationLedgerSegment.visible_through_message_position.isnot(None),
                            AgentMessage.position
                            <= ConversationLedgerSegment.visible_through_message_position,
                        ),
                    )
                )
                .group_by(AgentConversation.id, AgentConversation.updated_at)
            )

            if cursor_rank is not None and cursor_ts and cursor_uuid:
                base_query = base_query.having(
                    or_(
                        func.max(rank_expr) < cursor_rank,
                        and_(
                            func.max(rank_expr) == cursor_rank,
                            or_(
                                AgentConversation.updated_at < cursor_ts,
                                and_(
                                    AgentConversation.updated_at == cursor_ts,
                                    AgentConversation.id < cursor_uuid,
                                ),
                            ),
                        ),
                    )
                )

            ranked = base_query.subquery()

            result = await session.execute(
                select(AgentConversation, ranked.c.rank)
                .join(ranked, AgentConversation.id == ranked.c.cid)
                .order_by(
                    ranked.c.rank.desc(),
                    AgentConversation.updated_at.desc(),
                    AgentConversation.id.desc(),
                )
                .limit(limit + 1)
            )

            rows = result.all()
            next_cursor = None
            if len(rows) > limit:
                rows = rows[:limit]
                tail_conv, tail_rank = rows[-1]
                next_cursor = encode_search_cursor(
                    float(tail_rank or 0.0), tail_conv.updated_at, tail_conv.id
                )

            if not rows:
                return ConversationSearchPage(items=[], next_cursor=None)

            ids = [row[0].id for row in rows]
            messages = await session.execute(
                select(AgentMessage)
                .join(
                    ConversationLedgerSegment,
                    ConversationLedgerSegment.id == AgentMessage.segment_id,
                )
                .where(AgentMessage.conversation_id.in_(ids))
                .where(
                    or_(
                        ConversationLedgerSegment.truncated_at.is_(None),
                        and_(
                            ConversationLedgerSegment.visible_through_message_position.isnot(None),
                            AgentMessage.position
                            <= ConversationLedgerSegment.visible_through_message_position,
                        ),
                    )
                )
                .order_by(AgentMessage.conversation_id, AgentMessage.position)
            )
            message_rows: Sequence[AgentMessage] = messages.scalars().all()
            grouped: dict[uuid.UUID, list[AgentMessage]] = {}
            for row in message_rows:
                grouped.setdefault(row.conversation_id, []).append(row)

            hits: list[ConversationSearchHit] = []
            for conversation, rank in rows:
                entries = grouped.get(conversation.id, [])
                hits.append(
                    ConversationSearchHit(
                        record=record_from_model(conversation, entries),
                        score=float(rank or 0.0),
                    )
                )

            return ConversationSearchPage(items=hits, next_cursor=next_cursor)


__all__ = ["ConversationSearchStore"]
