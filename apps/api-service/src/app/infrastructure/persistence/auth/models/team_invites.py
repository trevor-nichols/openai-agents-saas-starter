"""Tenant member invite ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.team import TeamInviteStatus
from app.infrastructure.persistence.models.base import UTC_NOW, Base, uuid_pk
from app.infrastructure.persistence.types import CITEXTCompat


class TenantMemberInvite(Base):
    """Invites issued by tenant admins to add members."""

    __tablename__ = "tenant_member_invites"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_tenant_member_invites_token_hash"),
        Index("ix_tenant_member_invites_tenant_status", "tenant_id", "status"),
        Index("ix_tenant_member_invites_email", "invited_email"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenant_accounts.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    token_hint: Mapped[str] = mapped_column(String(16), nullable=False)
    invited_email: Mapped[str] = mapped_column(CITEXTCompat(), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[TeamInviteStatus] = mapped_column(
        SAEnum(
            TeamInviteStatus,
            name="tenant_member_invite_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=TeamInviteStatus.ACTIVE,
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    accepted_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_reason: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW, onupdate=UTC_NOW
    )


__all__ = ["TenantMemberInvite"]
