"""Conversation ledger read store (public_sse_v1 replay).

The durable ledger persists every `public_sse_v1` frame emitted to the frontend.
This module implements the query/read path to replay those frames deterministically.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.conversations import ConversationNotFoundError
from app.infrastructure.persistence.conversations.cursors import (
    decode_ledger_event_cursor,
    encode_ledger_event_cursor,
)
from app.infrastructure.persistence.conversations.ids import (
    coerce_conversation_uuid,
    parse_tenant_id,
)
from app.infrastructure.persistence.conversations.ledger_models import (
    ConversationLedgerEvent,
    ConversationLedgerSegment,
)
from app.infrastructure.persistence.conversations.models import AgentConversation


@dataclass(slots=True)
class ConversationLedgerEventRef:
    """Minimal event reference for replay (payload inline or spilled)."""

    id: int
    payload_json: dict[str, Any] | None
    payload_object_id: uuid.UUID | None
    payload_size_bytes: int


@dataclass(slots=True)
class _SegmentVisibility:
    segment_id: uuid.UUID
    max_event_row_id: int | None


class ConversationLedgerQueryStore:
    """Read-optimized access for the durable conversation ledger."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def has_container_file_citation(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        container_id: str,
        file_id: str,
    ) -> bool:
        """Return True if a visible ledger event cites the given container file.

        This is used for access control when proxying downloads of Code Interpreter
        container files created in auto containers (which may not be persisted as
        explicit Container rows).
        """

        conversation_uuid = coerce_conversation_uuid(conversation_id)
        tenant_uuid = parse_tenant_id(tenant_id)

        container_id = (container_id or "").strip()
        file_id = (file_id or "").strip()
        if not container_id or not file_id:
            return False

        async with self._session_factory() as session:
            conversation = await session.get(AgentConversation, conversation_uuid)
            if conversation is None or conversation.tenant_id != tenant_uuid:
                raise ConversationNotFoundError(
                    f"Conversation {conversation_id} does not exist"
                )

            segments = await self._visible_segments(
                session,
                tenant_id=tenant_uuid,
                conversation_id=conversation_uuid,
            )
            if not segments:
                return False

            visibility_predicate = self._segment_visibility_predicate(segments)

            citation = ConversationLedgerEvent.payload_json["citation"]
            stmt = (
                select(ConversationLedgerEvent.id)
                .where(
                    ConversationLedgerEvent.tenant_id == tenant_uuid,
                    ConversationLedgerEvent.conversation_id == conversation_uuid,
                    ConversationLedgerEvent.kind == "message.citation",
                    ConversationLedgerEvent.payload_json.is_not(None),
                    visibility_predicate,
                    citation["type"].as_string() == "container_file_citation",
                    citation["container_id"].as_string() == container_id,
                    citation["file_id"].as_string() == file_id,
                )
                .limit(1)
            )
            found = await session.execute(stmt)
            return found.scalar_one_or_none() is not None

    async def list_events_page(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        limit: int,
        cursor: str | None,
    ) -> tuple[list[ConversationLedgerEventRef], str | None]:
        conversation_uuid = coerce_conversation_uuid(conversation_id)
        tenant_uuid = parse_tenant_id(tenant_id)

        limit = max(1, min(int(limit), 1000))
        start_after_id = decode_ledger_event_cursor(cursor) if cursor else 0

        async with self._session_factory() as session:
            conversation = await session.get(AgentConversation, conversation_uuid)
            if conversation is None or conversation.tenant_id != tenant_uuid:
                raise ConversationNotFoundError(f"Conversation {conversation_id} does not exist")

            segments = await self._visible_segments(
                session,
                tenant_id=tenant_uuid,
                conversation_id=conversation_uuid,
            )
            if not segments:
                return [], None

            visibility_predicate = self._segment_visibility_predicate(segments)

            stmt = (
                select(ConversationLedgerEvent)
                .where(
                    ConversationLedgerEvent.tenant_id == tenant_uuid,
                    ConversationLedgerEvent.conversation_id == conversation_uuid,
                    ConversationLedgerEvent.id > start_after_id,
                    visibility_predicate,
                )
                .order_by(ConversationLedgerEvent.id.asc())
                .limit(limit + 1)
            )

            result = await session.execute(stmt)
            rows = list(result.scalars().all())

            has_extra = len(rows) > limit
            rows = rows[:limit]

            next_cursor = None
            if has_extra and rows:
                next_cursor = encode_ledger_event_cursor(rows[-1].id)

            items: list[ConversationLedgerEventRef] = []
            for row in rows:
                items.append(
                    ConversationLedgerEventRef(
                        id=row.id,
                        payload_json=row.payload_json,
                        payload_object_id=row.payload_object_id,
                        payload_size_bytes=row.payload_size_bytes,
                    )
                )
            return items, next_cursor

    async def _visible_segments(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> list[_SegmentVisibility]:
        result = await session.execute(
            select(ConversationLedgerSegment)
            .where(
                ConversationLedgerSegment.tenant_id == tenant_id,
                ConversationLedgerSegment.conversation_id == conversation_id,
            )
            .order_by(ConversationLedgerSegment.segment_index.asc())
        )
        segments = list(result.scalars().all())
        if not segments:
            return []

        active = [seg for seg in segments if seg.truncated_at is None]
        if len(active) > 1:
            raise ValueError("Conversation ledger has multiple active segments")
        active_segment_id = active[0].id if active else None

        visible: list[_SegmentVisibility] = []
        for seg in segments:
            if seg.truncated_at is None:
                if active_segment_id is not None and seg.id != active_segment_id:
                    raise ValueError(
                        "Conversation ledger contains unexpected active segment ordering"
                    )
                visible.append(_SegmentVisibility(segment_id=seg.id, max_event_row_id=None))
                continue

            if seg.visible_through_event_id is None:
                raise ValueError("Truncated ledger segment missing visible_through_event_id")
            visible.append(
                _SegmentVisibility(
                    segment_id=seg.id,
                    max_event_row_id=int(seg.visible_through_event_id),
                )
            )

        return visible

    def _segment_visibility_predicate(self, segments: list[_SegmentVisibility]):
        conditions = []
        for seg in segments:
            if seg.max_event_row_id is None:
                conditions.append(ConversationLedgerEvent.segment_id == seg.segment_id)
            else:
                conditions.append(
                    and_(
                        ConversationLedgerEvent.segment_id == seg.segment_id,
                        ConversationLedgerEvent.id <= seg.max_event_row_id,
                    )
                )
        return or_(*conditions) if conditions else ConversationLedgerEvent.id < 0


__all__ = ["ConversationLedgerEventRef", "ConversationLedgerQueryStore"]
