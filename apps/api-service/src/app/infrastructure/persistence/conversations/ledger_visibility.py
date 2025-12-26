"""Shared visibility helpers for conversation message queries."""

from __future__ import annotations

import uuid

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.conversations.ledger_models import ConversationLedgerSegment
from app.infrastructure.persistence.conversations.models import AgentMessage


def visible_message_clause():
    """Clause for message visibility when joined with ConversationLedgerSegment."""

    return or_(
        ConversationLedgerSegment.truncated_at.is_(None),
        and_(
            ConversationLedgerSegment.visible_through_message_position.isnot(None),
            AgentMessage.position <= ConversationLedgerSegment.visible_through_message_position,
        ),
    )


async def load_ledger_segments(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    conversation_id: uuid.UUID,
) -> list[ConversationLedgerSegment]:
    result = await session.execute(
        select(ConversationLedgerSegment)
        .where(
            ConversationLedgerSegment.tenant_id == tenant_id,
            ConversationLedgerSegment.conversation_id == conversation_id,
        )
        .order_by(ConversationLedgerSegment.segment_index.asc())
    )
    return list(result.scalars().all())


async def load_ledger_segments_bulk(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    conversation_ids: list[uuid.UUID],
) -> list[ConversationLedgerSegment]:
    if not conversation_ids:
        return []
    result = await session.execute(
        select(ConversationLedgerSegment)
        .where(
            ConversationLedgerSegment.tenant_id == tenant_id,
            ConversationLedgerSegment.conversation_id.in_(conversation_ids),
        )
        .order_by(
            ConversationLedgerSegment.conversation_id.asc(),
            ConversationLedgerSegment.segment_index.asc(),
        )
    )
    return list(result.scalars().all())


def build_message_visibility_predicate(segments: list[ConversationLedgerSegment]):
    """Build a SQL predicate that selects only the visible portion of each segment."""

    if not segments:
        return AgentMessage.id >= 0  # all messages (fallback; normally segments always exist)

    active_by_conversation: dict[uuid.UUID, int] = {}
    for seg in segments:
        if seg.truncated_at is None:
            active_by_conversation[seg.conversation_id] = (
                active_by_conversation.get(seg.conversation_id, 0) + 1
            )
    if any(count > 1 for count in active_by_conversation.values()):
        raise ValueError("Conversation ledger has multiple active segments")

    conditions = []
    for seg in segments:
        if seg.truncated_at is None:
            conditions.append(AgentMessage.segment_id == seg.id)
            continue

        max_pos = seg.visible_through_message_position
        if max_pos is None:
            raise ValueError("Truncated ledger segment missing visible_through_message_position")
        conditions.append(and_(AgentMessage.segment_id == seg.id, AgentMessage.position <= max_pos))

    return or_(*conditions) if conditions else AgentMessage.id < 0


__all__ = [
    "build_message_visibility_predicate",
    "load_ledger_segments",
    "load_ledger_segments_bulk",
    "visible_message_clause",
]
