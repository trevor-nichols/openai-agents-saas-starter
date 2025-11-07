"""SQLAlchemy models for auth persistence (users, memberships, tokens)."""

from __future__ import annotations

from enum import Enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import CITEXT, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import Base, UTC_NOW, uuid_pk

if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from app.infrastructure.persistence.conversations.models import (
        AgentConversation,
        TenantAccount,
    )


class UserStatus(str, Enum):
    """Enumeration of supported lifecycle states for human users."""

    PENDING = "pending"
    ACTIVE = "active"
    DISABLED = "disabled"
    LOCKED = "locked"


class UserAccount(Base):
    """Human identity stored in Postgres."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        Index("ix_users_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk
    )
    email: Mapped[str] = mapped_column(CITEXT(), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    password_pepper_version: Mapped[str] = mapped_column(
        String(32), nullable=False, default="v1"
    )
    status: Mapped[UserStatus] = mapped_column(
        SAEnum(
            UserStatus,
            name="user_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=UserStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW, onupdate=UTC_NOW
    )

    profile: Mapped["UserProfile | None"] = relationship(
        "UserProfile", back_populates="user", uselist=False
    )
    memberships: Mapped[list["TenantUserMembership"]] = relationship(
        "TenantUserMembership",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    tenants: Mapped[list["TenantAccount"]] = relationship(
        "TenantAccount",
        secondary="tenant_user_memberships",
        back_populates="users",
        viewonly=True,
    )
    conversations: Mapped[list["AgentConversation"]] = relationship(
        "AgentConversation",
        back_populates="user",
        viewonly=True,
    )
    password_history: Mapped[list["PasswordHistory"]] = relationship(
        "PasswordHistory",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    login_events: Mapped[list["UserLoginEvent"]] = relationship(
        "UserLoginEvent",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserProfile(Base):
    """Optional profile information for display purposes."""

    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    display_name: Mapped[str | None] = mapped_column(String(128))
    given_name: Mapped[str | None] = mapped_column(String(64))
    family_name: Mapped[str | None] = mapped_column(String(64))
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    timezone: Mapped[str | None] = mapped_column(String(64))
    locale: Mapped[str | None] = mapped_column(String(32))
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW, onupdate=UTC_NOW
    )

    user: Mapped[UserAccount] = relationship(back_populates="profile")


class TenantUserMembership(Base):
    """Association between a user and a tenant with role metadata."""

    __tablename__ = "tenant_user_memberships"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "tenant_id", name="uq_tenant_user_memberships_user_tenant"
        ),
        Index("ix_tenant_user_memberships_tenant_role", "tenant_id", "role"),
        Index("ix_tenant_user_memberships_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenant_accounts.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )

    user: Mapped[UserAccount] = relationship(back_populates="memberships")
    tenant: Mapped["TenantAccount"] = relationship(back_populates="memberships")


class PasswordHistory(Base):
    """Historical password hashes retained for reuse detection."""

    __tablename__ = "password_history"
    __table_args__ = (
        Index("ix_password_history_user_created", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    password_pepper_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )

    user: Mapped[UserAccount] = relationship(back_populates="password_history")


class UserLoginEvent(Base):
    """Immutable audit log for human login attempts."""

    __tablename__ = "user_login_events"
    __table_args__ = (
        Index("ix_user_login_events_user_created", "user_id", "created_at"),
        Index("ix_user_login_events_tenant_created", "tenant_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tenant_accounts.id", ondelete="SET NULL"), nullable=True
    )
    ip_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(512))
    result: Mapped[str] = mapped_column(String(16), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )

    user: Mapped[UserAccount] = relationship(back_populates="login_events")


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


# Ensure the SQLAlchemy registry is aware of tenant models before relationship configuration.
from app.infrastructure.persistence.conversations.models import TenantAccount  # noqa: E402,F401
