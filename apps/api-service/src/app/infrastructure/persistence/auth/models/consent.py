"""Consent and notification preference ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import UTC_NOW, Base, uuid_pk

if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from app.infrastructure.persistence.auth.models.user import UserAccount
    from app.infrastructure.persistence.tenants.models import TenantAccount


class UserConsent(Base):
    """Versioned acceptance of policies or terms."""

    __tablename__ = "user_consents"
    __table_args__ = (
        UniqueConstraint("user_id", "policy_key", "version", name="uq_user_consents_version"),
        Index("ix_user_consents_user_policy", "user_id", "policy_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    policy_key: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )
    ip_hash: Mapped[str | None] = mapped_column(String(128))
    user_agent_hash: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )

    user: Mapped[UserAccount] = relationship(back_populates="consents")


class UserNotificationPreference(Base):
    """Channel/category preferences with optional tenant scoping."""

    __tablename__ = "user_notification_preferences"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "tenant_id",
            "channel",
            "category",
            name="uq_user_notification_preferences_scope",
        ),
        Index("ix_user_notification_preferences_user", "user_id"),
        Index("ix_user_notification_preferences_tenant", "tenant_id"),
        Index(
            "uq_user_notification_preferences_null_tenant",
            "user_id",
            "channel",
            "category",
            unique=True,
            postgresql_where=text("tenant_id IS NULL"),
            sqlite_where=text("tenant_id IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tenant_accounts.id", ondelete="CASCADE"), nullable=True
    )
    channel: Mapped[str] = mapped_column(String(16), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW, onupdate=UTC_NOW
    )

    user: Mapped[UserAccount] = relationship(back_populates="notification_preferences")
    tenant: Mapped[TenantAccount | None] = relationship("TenantAccount")
