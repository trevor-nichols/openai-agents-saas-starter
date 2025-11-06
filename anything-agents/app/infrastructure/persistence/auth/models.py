"""SQLAlchemy models for stored refresh tokens and revocations."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import Base, UTC_NOW, uuid_pk


class ServiceAccountToken(Base):
    """Persisted refresh token metadata for service accounts."""

    __tablename__ = "service_account_tokens"
    __table_args__ = (
        UniqueConstraint("refresh_jti", name="uq_service_account_tokens_jti"),
        Index(
            "uq_service_account_tokens_active_key",
            "account",
            "tenant_id",
            "scope_key",
            unique=True,
            postgresql_where=text("revoked_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk
    )
    account: Mapped[str] = mapped_column(String(128), nullable=False)
    tenant_id: Mapped[str | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    scope_key: Mapped[str] = mapped_column(String(256), nullable=False)
    scopes: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    refresh_token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_jti: Mapped[str] = mapped_column(String(64), nullable=False)
    signing_kid: Mapped[str] = mapped_column(String(64), nullable=False, default="legacy-hs256")
    fingerprint: Mapped[str | None] = mapped_column(String(128))
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
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
