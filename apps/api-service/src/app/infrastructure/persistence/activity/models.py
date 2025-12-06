"""SQLAlchemy models for activity/audit events."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import UTC_NOW, Base, uuid_pk


class ActivityEventRow(Base):
    __tablename__ = "activity_events"
    __table_args__ = (
        Index("ix_activity_events_tenant_created", "tenant_id", "created_at"),
        Index("ix_activity_events_tenant_action", "tenant_id", "action"),
        Index("ix_activity_events_object", "tenant_id", "object_type", "object_id"),
        Index("ix_activity_events_request", "request_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tenant_accounts.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(96), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    actor_type: Mapped[str | None] = mapped_column(String(16))
    actor_role: Mapped[str | None] = mapped_column(String(32))
    object_type: Mapped[str | None] = mapped_column(String(64))
    object_id: Mapped[str | None] = mapped_column(String(128))
    object_name: Mapped[str | None] = mapped_column(String(256))
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="success")
    source: Mapped[str | None] = mapped_column(String(32))
    request_id: Mapped[str | None] = mapped_column(String(128))
    ip_hash: Mapped[str | None] = mapped_column(String(128))
    user_agent: Mapped[str | None] = mapped_column(String(512))
    metadata_json: Mapped[dict[str, object] | None] = mapped_column("metadata", JSON, nullable=True)


class ActivityReceiptRow(Base):
    __tablename__ = "activity_event_receipts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "event_id", name="uq_activity_receipt"),
        Index("ix_activity_receipts_user_status", "tenant_id", "user_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tenant_accounts.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("activity_events.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=UTC_NOW,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=UTC_NOW,
    )


class ActivityLastSeenRow(Base):
    __tablename__ = "activity_last_seen"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_activity_last_seen_user"),
        Index("ix_activity_last_seen_user", "tenant_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tenant_accounts.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    last_seen_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=UTC_NOW,
    )
    last_seen_event_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=UTC_NOW,
    )


__all__ = ["ActivityEventRow", "ActivityReceiptRow", "ActivityLastSeenRow"]
