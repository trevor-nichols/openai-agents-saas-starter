"""Signup invite and request ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
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

    approved_invite: Mapped["TenantSignupInvite" | None] = relationship(
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

    source_request: Mapped["TenantSignupRequest" | None] = relationship(
        "TenantSignupRequest",
        back_populates="approved_invite",
        uselist=False,
        primaryjoin="TenantSignupInvite.signup_request_id == TenantSignupRequest.id",
    )
    reservations: Mapped[list["TenantSignupInviteReservation"]] = relationship(
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

    invite: Mapped["TenantSignupInvite"] = relationship(
        "TenantSignupInvite",
        back_populates="reservations",
    )
