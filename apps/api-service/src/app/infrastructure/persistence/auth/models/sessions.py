"""Session and refresh token ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import UTC_NOW, Base, uuid_pk
from app.infrastructure.persistence.types import JSONBCompat

if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from app.infrastructure.persistence.auth.models.user import UserAccount


class UserSession(Base):
    """Normalized device/session metadata for active user refresh tokens."""

    __tablename__ = "user_sessions"
    __table_args__ = (
        Index("ix_user_sessions_user_last_seen", "user_id", "last_seen_at"),
        Index("ix_user_sessions_tenant_last_seen", "tenant_id", "last_seen_at"),
        Index("ix_user_sessions_refresh_jti", "refresh_jti", unique=True),
        Index("ix_user_sessions_fingerprint", "user_id", "fingerprint"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenant_accounts.id", ondelete="CASCADE"), nullable=False
    )
    refresh_jti: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    fingerprint: Mapped[str | None] = mapped_column(String(256))
    ip_hash: Mapped[str | None] = mapped_column(String(128))
    ip_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    ip_masked: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(512))
    client_platform: Mapped[str | None] = mapped_column(String(64))
    client_browser: Mapped[str | None] = mapped_column(String(64))
    client_device: Mapped[str | None] = mapped_column(String(32))
    location_city: Mapped[str | None] = mapped_column(String(128))
    location_region: Mapped[str | None] = mapped_column(String(128))
    location_country: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW, onupdate=UTC_NOW
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_reason: Mapped[str | None] = mapped_column(String(256))

    user: Mapped[UserAccount] = relationship(back_populates="sessions")
    refresh_token: Mapped[ServiceAccountToken | None] = relationship(
        "ServiceAccountToken",
        back_populates="session",
        uselist=False,
    )


class ServiceAccountToken(Base):
    """Persisted refresh token metadata for service accounts."""

    __tablename__ = "service_account_tokens"
    __table_args__ = (
        UniqueConstraint("refresh_jti", name="uq_service_account_tokens_jti"),
        Index(
            "uq_service_account_tokens_active_service_accounts",
            "account",
            "tenant_id",
            "scope_key",
            unique=True,
            postgresql_where=text("revoked_at IS NULL AND account NOT LIKE 'user:%'"),
            sqlite_where=text("revoked_at IS NULL AND account NOT LIKE 'user:%'"),
        ),
        Index("ix_service_account_tokens_session_id", "session_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    account: Mapped[str] = mapped_column(String(128), nullable=False)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    scope_key: Mapped[str] = mapped_column(String(256), nullable=False)
    scopes: Mapped[list[str]] = mapped_column(JSONBCompat, nullable=False)
    refresh_token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_jti: Mapped[str] = mapped_column(String(64), nullable=False)
    signing_kid: Mapped[str] = mapped_column(String(64), nullable=False)
    fingerprint: Mapped[str | None] = mapped_column(String(128))
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("user_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_reason: Mapped[str | None] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW, onupdate=UTC_NOW
    )

    def mark_revoked(self, *, reason: str | None = None, timestamp: datetime | None = None) -> None:
        self.revoked_at = timestamp or datetime.utcnow()
        self.revoked_reason = reason

    session: Mapped[UserSession | None] = relationship(
        "UserSession",
        back_populates="refresh_token",
        uselist=False,
    )
