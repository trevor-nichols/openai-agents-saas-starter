"""ORM models for Stripe webhooks and event storage."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

# Ensure dependent ORM models register before SQLAlchemy configures relationship
# targets when Stripe models load in isolation (e.g., billing stream unit tests).
from app.infrastructure.persistence.billing import models as _billing_models  # noqa: F401
from app.infrastructure.persistence.conversations import (  # noqa: F401
    models as _conversation_models,
)
from app.infrastructure.persistence.models.base import UTC_NOW, Base, uuid_pk
from app.infrastructure.persistence.tenants import models as _tenant_models  # noqa: F401
from app.infrastructure.persistence.types import JSONBCompat


class StripeEventStatus(str, Enum):
    RECEIVED = "received"
    PROCESSED = "processed"
    FAILED = "failed"


class StripeEvent(Base):
    """Raw Stripe webhook payload persistence for auditing and replay."""

    __tablename__ = "stripe_events"
    __table_args__ = (
        Index("ix_stripe_events_type", "event_type"),
        Index("ix_stripe_events_status", "processing_outcome"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    stripe_event_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONBCompat, nullable=False)
    tenant_hint: Mapped[str | None] = mapped_column(String(64))
    stripe_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processing_outcome: Mapped[str] = mapped_column(
        String(32), default=StripeEventStatus.RECEIVED.value, nullable=False
    )
    processing_error: Mapped[str | None] = mapped_column(Text)
    processing_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class StripeDispatchStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    FAILED = "failed"
    COMPLETED = "completed"


class StripeEventDispatch(Base):
    """Per-handler dispatch records for Stripe events."""

    __tablename__ = "stripe_event_dispatch"
    __table_args__ = (
        Index("ix_stripe_event_dispatch_handler_status", "handler", "status", "next_retry_at"),
        UniqueConstraint("stripe_event_id", "handler", name="uq_stripe_event_dispatch_handler"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    stripe_event_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("stripe_events.id", ondelete="CASCADE"),
        nullable=False,
    )
    handler: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=StripeDispatchStatus.PENDING.value, nullable=False
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, onupdate=UTC_NOW, nullable=False
    )
