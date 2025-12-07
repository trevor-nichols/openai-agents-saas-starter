"""SQLAlchemy models for auth persistence (users, memberships, tokens)."""

from __future__ import annotations

import importlib
import uuid
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.signup import (
    SignupInviteReservationStatus,
    SignupInviteStatus,
    SignupRequestStatus,
)
from app.infrastructure.persistence.models.base import UTC_NOW, Base, uuid_pk
from app.infrastructure.persistence.types import CITEXTCompat, JSONBCompat

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
    tenants: Mapped[list[TenantAccount]] = relationship(
        "TenantAccount",
        secondary="tenant_user_memberships",
        back_populates="users",
        viewonly=True,
    )
    conversations: Mapped[list[AgentConversation]] = relationship(
        "AgentConversation",
        back_populates="user",
        viewonly=True,
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
    usage_counters: Mapped[list[UsageCounter]] = relationship(
        "UsageCounter",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserProfile(Base):
    """Optional profile information for display purposes."""

    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
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


class TenantUserMembership(Base):
    """Association between a user and a tenant with role metadata."""

    __tablename__ = "tenant_user_memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "tenant_id", name="uq_tenant_user_memberships_user_tenant"),
        Index("ix_tenant_user_memberships_tenant_role", "tenant_id", "role"),
        Index("ix_tenant_user_memberships_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
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
    tenant: Mapped[TenantAccount] = relationship(back_populates="memberships")


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


class TenantSignupRequest(Base):
    """Requests submitted when deployments run in invite-only or approval modes."""

    __tablename__ = "tenant_signup_requests"
    __table_args__ = (
        Index("ix_tenant_signup_requests_status", "status"),
        Index("ix_tenant_signup_requests_email", "email"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    email: Mapped[str] = mapped_column(CITEXTCompat(), nullable=False)
    organization: Mapped[str | None] = mapped_column(String(128))
    full_name: Mapped[str | None] = mapped_column(String(128))
    message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[SignupRequestStatus] = mapped_column(
        SAEnum(
            SignupRequestStatus,
            name="tenant_signup_request_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=SignupRequestStatus.PENDING,
    )
    decision_reason: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decided_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    invite_token_hint: Mapped[str | None] = mapped_column(String(16))
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(512))
    honeypot_value: Mapped[str | None] = mapped_column(String(64))
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONBCompat, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW, onupdate=UTC_NOW
    )

    approved_invite: Mapped[TenantSignupInvite | None] = relationship(
        "TenantSignupInvite",
        back_populates="source_request",
        uselist=False,
        primaryjoin="TenantSignupRequest.id == TenantSignupInvite.signup_request_id",
    )


class TenantSignupInvite(Base):
    """Invites issued by operators to gate signup flows."""

    __tablename__ = "tenant_signup_invites"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_tenant_signup_invites_token_hash"),
        Index("ix_tenant_signup_invites_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    token_hint: Mapped[str] = mapped_column(String(16), nullable=False)
    invited_email: Mapped[str | None] = mapped_column(CITEXTCompat())
    issuer_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    issuer_tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tenant_accounts.id", ondelete="SET NULL"), nullable=True
    )
    signup_request_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tenant_signup_requests.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[SignupInviteStatus] = mapped_column(
        SAEnum(
            SignupInviteStatus,
            name="tenant_signup_invite_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=SignupInviteStatus.ACTIVE,
    )
    max_redemptions: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    redeemed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_redeemed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_reason: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONBCompat, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW, onupdate=UTC_NOW
    )

    source_request: Mapped[TenantSignupRequest | None] = relationship(
        TenantSignupRequest,
        back_populates="approved_invite",
        uselist=False,
        primaryjoin="TenantSignupInvite.signup_request_id == TenantSignupRequest.id",
    )
    reservations: Mapped[list[TenantSignupInviteReservation]] = relationship(
        "TenantSignupInviteReservation",
        back_populates="invite",
        cascade="all, delete-orphan",
    )


class TenantSignupInviteReservation(Base):
    """Tracks in-flight invite reservations while signup completes."""

    __tablename__ = "tenant_signup_invite_reservations"
    __table_args__ = (
        Index("ix_signup_invite_reservations_status", "status"),
        Index("ix_signup_invite_reservations_invite_status", "invite_id", "status"),
        Index("ix_signup_invite_reservations_expires", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    invite_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenant_signup_invites.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(CITEXTCompat(), nullable=False)
    status: Mapped[SignupInviteReservationStatus] = mapped_column(
        SAEnum(
            SignupInviteReservationStatus,
            name="signup_invite_reservation_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=SignupInviteReservationStatus.ACTIVE,
    )
    reserved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    released_reason: Mapped[str | None] = mapped_column(Text)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tenant_accounts.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW, onupdate=UTC_NOW
    )

    invite: Mapped[TenantSignupInvite] = relationship(
        "TenantSignupInvite",
        back_populates="reservations",
    )


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
    # Avoid tenant back-population to keep the tenant model unchanged.
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
        ),
        Index("ix_service_account_tokens_session_id", "session_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    account: Mapped[str] = mapped_column(String(128), nullable=False)
    tenant_id: Mapped[str | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
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


class MfaMethodType(str, Enum):
    """Supported MFA factor types."""

    TOTP = "totp"
    WEBAUTHN = "webauthn"


class UserMfaMethod(Base):
    """Registered multi-factor authentication method for a user."""

    __tablename__ = "user_mfa_methods"
    __table_args__ = (
        UniqueConstraint("user_id", "label", name="uq_user_mfa_methods_label"),
        Index("ix_user_mfa_methods_user_type", "user_id", "method_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    method_type: Mapped[MfaMethodType] = mapped_column(
        SAEnum(
            MfaMethodType,
            name="mfa_method_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    label: Mapped[str | None] = mapped_column(String(64))
    secret_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    credential_json: Mapped[dict[str, object] | None] = mapped_column(JSONBCompat)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_reason: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW, onupdate=UTC_NOW
    )

    user: Mapped[UserAccount] = relationship(back_populates="mfa_methods")


class UserRecoveryCode(Base):
    """Single-use recovery code hash tied to a user."""

    __tablename__ = "user_recovery_codes"
    __table_args__ = (
        Index("ix_user_recovery_codes_user", "user_id"),
        Index("ix_user_recovery_codes_used", "used_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    code_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )

    user: Mapped[UserAccount] = relationship(back_populates="recovery_codes")


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


class UsageCounterGranularity(str, Enum):
    """Bucket size for usage summaries."""

    DAY = "day"
    MONTH = "month"


class UsageCounter(Base):
    """Aggregated usage snapshot for billing/analytics."""

    __tablename__ = "usage_counters"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "user_id",
            "period_start",
            "granularity",
            name="uq_usage_counters_bucket",
        ),
        Index("ix_usage_counters_tenant_period", "tenant_id", "period_start"),
        Index("ix_usage_counters_user_period", "user_id", "period_start"),
        Index(
            "uq_usage_counters_tenant_period_null_user",
            "tenant_id",
            "period_start",
            "granularity",
            unique=True,
            postgresql_where=text("user_id IS NULL"),
            sqlite_where=text("user_id IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenant_accounts.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    granularity: Mapped[UsageCounterGranularity] = mapped_column(
        SAEnum(
            UsageCounterGranularity,
            name="usage_counter_granularity",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    input_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    requests: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    storage_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW, onupdate=UTC_NOW
    )

    user: Mapped[UserAccount | None] = relationship(back_populates="usage_counters")
    tenant: Mapped[TenantAccount] = relationship("TenantAccount")


class SecurityEvent(Base):
    """Normalized security/audit events (e.g., password change, MFA update)."""

    __tablename__ = "security_events"
    __table_args__ = (
        Index("ix_security_events_user_created", "user_id", "created_at"),
        Index("ix_security_events_tenant_created", "tenant_id", "created_at"),
        Index("ix_security_events_type", "event_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tenant_accounts.id", ondelete="SET NULL"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str | None] = mapped_column(String(32))
    ip_hash: Mapped[str | None] = mapped_column(String(128))
    user_agent_hash: Mapped[str | None] = mapped_column(String(128))
    request_id: Mapped[str | None] = mapped_column(String(128))
    metadata_json: Mapped[dict[str, object] | None] = mapped_column(JSONBCompat)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )

    user: Mapped[UserAccount | None] = relationship(back_populates="security_events")
    tenant: Mapped[TenantAccount | None] = relationship("TenantAccount")


# Ensure the SQLAlchemy registry is aware of tenant models before relationship configuration.
importlib.import_module("app.infrastructure.persistence.conversations.models")
