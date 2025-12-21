"""Security event ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import UTC_NOW, Base, uuid_pk
from app.infrastructure.persistence.types import JSONBCompat

if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from app.infrastructure.persistence.auth.models.user import UserAccount
    from app.infrastructure.persistence.tenants.models import TenantAccount


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
