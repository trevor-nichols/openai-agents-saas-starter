"""User and identity ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import UTC_NOW, Base, uuid_pk
from app.infrastructure.persistence.types import CITEXTCompat, JSONBCompat

if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from app.infrastructure.persistence.auth.models.consent import (
        UserConsent,
        UserNotificationPreference,
    )
    from app.infrastructure.persistence.auth.models.membership import TenantUserMembership
    from app.infrastructure.persistence.auth.models.mfa import UserMfaMethod, UserRecoveryCode
    from app.infrastructure.persistence.auth.models.security import SecurityEvent
    from app.infrastructure.persistence.auth.models.sessions import UserSession


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

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    email: Mapped[str] = mapped_column(CITEXTCompat(), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    password_pepper_version: Mapped[str] = mapped_column(String(32), nullable=False, default="v2")
    status: Mapped[UserStatus] = mapped_column(
        SAEnum(
            UserStatus,
            name="user_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=UserStatus.PENDING,
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW, onupdate=UTC_NOW
    )

    profile: Mapped[UserProfile | None] = relationship(
        "UserProfile", back_populates="user", uselist=False
    )
    memberships: Mapped[list[TenantUserMembership]] = relationship(
        "TenantUserMembership",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    password_history: Mapped[list[PasswordHistory]] = relationship(
        "PasswordHistory",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    login_events: Mapped[list[UserLoginEvent]] = relationship(
        "UserLoginEvent",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    sessions: Mapped[list[UserSession]] = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    mfa_methods: Mapped[list[UserMfaMethod]] = relationship(
        "UserMfaMethod",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    recovery_codes: Mapped[list[UserRecoveryCode]] = relationship(
        "UserRecoveryCode",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    consents: Mapped[list[UserConsent]] = relationship(
        "UserConsent",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    notification_preferences: Mapped[list[UserNotificationPreference]] = relationship(
        "UserNotificationPreference",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    security_events: Mapped[list[SecurityEvent]] = relationship(
        "SecurityEvent",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserProfile(Base):
    """Optional profile information for display purposes."""

    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    display_name: Mapped[str | None] = mapped_column(String(128))
    given_name: Mapped[str | None] = mapped_column(String(64))
    family_name: Mapped[str | None] = mapped_column(String(64))
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    timezone: Mapped[str | None] = mapped_column(String(64))
    locale: Mapped[str | None] = mapped_column(String(32))
    metadata_json: Mapped[dict[str, str | None] | None] = mapped_column(JSONBCompat)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW, onupdate=UTC_NOW
    )

    user: Mapped[UserAccount] = relationship(back_populates="profile")


class PasswordHistory(Base):
    """Historical password hashes retained for reuse detection."""

    __tablename__ = "password_history"
    __table_args__ = (Index("ix_password_history_user_created", "user_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
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

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
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
