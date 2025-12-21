"""MFA ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, LargeBinary, String, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import UTC_NOW, Base, uuid_pk
from app.infrastructure.persistence.types import JSONBCompat

if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from app.infrastructure.persistence.auth.models.user import UserAccount


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
