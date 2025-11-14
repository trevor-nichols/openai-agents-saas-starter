"""SQLAlchemy models for status subscriptions."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, LargeBinary, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.status import SubscriptionChannel, SubscriptionSeverity, SubscriptionStatus
from app.infrastructure.persistence.models.base import UTC_NOW, Base


class StatusSubscriptionModel(Base):
    __tablename__ = "status_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    channel: Mapped[SubscriptionChannel] = mapped_column(String(16), nullable=False)
    target_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    target_masked: Mapped[str] = mapped_column(String(512), nullable=False)
    target_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    severity_filter: Mapped[SubscriptionSeverity] = mapped_column(
        String(16), nullable=False
    )
    status: Mapped[SubscriptionStatus] = mapped_column(String(32), nullable=False)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    verification_token_hash: Mapped[str | None] = mapped_column(
        String(128), nullable=True, index=True
    )
    verification_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    challenge_token_hash: Mapped[str | None] = mapped_column(
        String(128), nullable=True, index=True
    )
    webhook_secret_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    unsubscribe_token_hash: Mapped[str | None] = mapped_column(
        String(128), nullable=True, index=True
    )
    unsubscribe_token_encrypted: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True
    )
    revoked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=UTC_NOW)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, onupdate=UTC_NOW
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_challenge_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
