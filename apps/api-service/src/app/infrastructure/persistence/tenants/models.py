"""ORM models for tenant metadata/settings."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import UTC_NOW, Base, uuid_pk


class TenantAccount(Base):
    """Represents a customer tenant in a multi-tenant deployment."""

    __tablename__ = "tenant_accounts"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )


class TenantSettingsModel(Base):
    __tablename__ = "tenant_settings"
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_tenant_settings_tenant_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenant_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    billing_contacts_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=list,
    )
    billing_webhook_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    plan_metadata_json: Mapped[dict[str, str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    flags_json: Mapped[dict[str, bool]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, onupdate=UTC_NOW, nullable=False
    )

    tenant: Mapped[TenantAccount] = relationship("TenantAccount", lazy="selectin")


__all__ = ["TenantAccount", "TenantSettingsModel"]
