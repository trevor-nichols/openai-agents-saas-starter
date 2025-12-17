"""ORM models for the durable conversation ledger (public_sse_v1 persistence + replay).

This ledger is the canonical source of truth for replaying the exact UI transcript
state (including tool components) by storing the projected `public_sse_v1` frames
emitted to the frontend.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import INT_PK_TYPE, UTC_NOW, Base, uuid_pk
from app.infrastructure.persistence.types import JSONBCompat


class ConversationLedgerSegment(Base):
    """Represents a single visible lineage segment of a conversation transcript.

    A per-message deletion truncates the current segment at a boundary and starts a
    new segment; replay includes only the visible prefix of prior segments plus the
    full active segment.
    """

    __tablename__ = "conversation_ledger_segments"
    __table_args__ = (
        UniqueConstraint(
            "conversation_id",
            "segment_index",
            name="uq_conversation_ledger_segments_conversation_index",
        ),
        Index(
            "ix_conversation_ledger_segments_conversation_truncated",
            "conversation_id",
            "truncated_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenant_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agent_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    segment_index: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_segment_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversation_ledger_segments.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Ledger event id (conversation_ledger_events.id) of the last visible event in this segment.
    # Intentionally no FK to avoid circular dependencies between segment and event tables.
    visible_through_event_id: Mapped[int | None] = mapped_column(INT_PK_TYPE, nullable=True)
    # Message position (agent_messages.position) of the last visible message in this segment.
    # Used for per-message deletion to hide the truncated suffix without hard-delete.
    visible_through_message_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    truncated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, onupdate=UTC_NOW, nullable=False
    )


class ConversationLedgerEvent(Base):
    """Single persisted `public_sse_v1` frame (inline JSON or spilled to object storage)."""

    __tablename__ = "conversation_ledger_events"
    __table_args__ = (
        UniqueConstraint(
            "conversation_id",
            "stream_id",
            "event_id",
            name="uq_conversation_ledger_events_conversation_stream_event",
        ),
        Index(
            "ix_conversation_ledger_events_tenant_conversation_id_id",
            "tenant_id",
            "conversation_id",
            "id",
        ),
        Index("ix_conversation_ledger_events_tool_call_id", "tool_call_id"),
        Index("ix_conversation_ledger_events_item_id", "item_id"),
        CheckConstraint(
            "payload_json IS NOT NULL OR payload_object_id IS NOT NULL",
            name="ck_conversation_ledger_events_payload_present",
        ),
    )

    id: Mapped[int] = mapped_column(INT_PK_TYPE, primary_key=True, autoincrement=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenant_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agent_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    segment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversation_ledger_segments.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Public contract fields (selected for indexing / replay)
    schema_version: Mapped[str] = mapped_column(String(32), default="public_sse_v1", nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    stream_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_id: Mapped[int] = mapped_column(Integer, nullable=False)
    server_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    response_id: Mapped[str | None] = mapped_column(String(128))
    agent: Mapped[str | None] = mapped_column(String(64))
    workflow_run_id: Mapped[str | None] = mapped_column(String(64))
    provider_sequence_number: Mapped[int | None] = mapped_column(Integer)

    # Item/tool anchoring for stable tool cards and patch semantics
    output_index: Mapped[int | None] = mapped_column(Integer)
    item_id: Mapped[str | None] = mapped_column(String(255))
    content_index: Mapped[int | None] = mapped_column(Integer)
    tool_call_id: Mapped[str | None] = mapped_column(String(255))

    # Payload storage
    payload_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSONBCompat, nullable=True)
    payload_object_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("storage_objects.id", ondelete="SET NULL"),
        nullable=True,
    )

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )


class ConversationRunQueueItem(Base):
    """Durable FIFO queue item for user messages when a run is already active."""

    __tablename__ = "conversation_run_queue_items"
    __table_args__ = (
        Index(
            "ix_conversation_run_queue_items_conversation_status_id",
            "conversation_id",
            "status",
            "id",
        ),
        Index(
            "ix_conversation_run_queue_items_tenant_conversation_status_id",
            "tenant_id",
            "conversation_id",
            "status",
            "id",
        ),
    )

    id: Mapped[int] = mapped_column(INT_PK_TYPE, primary_key=True, autoincrement=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenant_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agent_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    segment_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversation_ledger_segments.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    status: Mapped[str] = mapped_column(String(16), default="queued", nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONBCompat, nullable=False)
    error_json: Mapped[dict[str, Any] | None] = mapped_column(JSONBCompat)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


__all__ = [
    "ConversationLedgerEvent",
    "ConversationLedgerSegment",
    "ConversationRunQueueItem",
]
