"""Shared helpers for conversation ledger segments.

Ledger segments model the visible lineage of a conversation transcript. They are used to:
- Persist public_sse_v1 replay frames in an append-only ledger.
- Apply user-driven truncation (per-message deletion) without hard-deleting immediately.

This module centralizes segment creation so both message persistence and ledger persistence
agree on the active segment for a conversation.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.conversations.ledger_models import ConversationLedgerSegment


async def get_or_create_active_segment(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    conversation_id: uuid.UUID,
) -> ConversationLedgerSegment:
    """Return the current active segment for a conversation, creating one if needed."""

    existing = await session.execute(
        select(ConversationLedgerSegment)
        .where(
            ConversationLedgerSegment.tenant_id == tenant_id,
            ConversationLedgerSegment.conversation_id == conversation_id,
            ConversationLedgerSegment.truncated_at.is_(None),
        )
        .order_by(ConversationLedgerSegment.segment_index.desc())
        .limit(1)
    )
    segment = existing.scalars().first()
    if segment is not None:
        return segment

    latest = await session.execute(
        select(ConversationLedgerSegment)
        .where(
            ConversationLedgerSegment.tenant_id == tenant_id,
            ConversationLedgerSegment.conversation_id == conversation_id,
        )
        .order_by(ConversationLedgerSegment.segment_index.desc())
        .limit(1)
    )
    parent = latest.scalars().first()
    next_index = int(parent.segment_index) + 1 if parent is not None else 0

    segment = ConversationLedgerSegment(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        segment_index=next_index,
        parent_segment_id=parent.id if parent is not None else None,
    )
    session.add(segment)
    await session.flush()
    return segment


__all__ = ["get_or_create_active_segment"]

