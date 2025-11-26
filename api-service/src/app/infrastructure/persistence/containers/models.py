"""SQLAlchemy ORM models for code interpreter containers and bindings."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import UTC_NOW, Base, uuid_pk
from app.infrastructure.persistence.types import JSONBCompat


class Container(Base):
    __tablename__ = "containers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", "deleted_at", name="uq_containers_tenant_name"),
        Index("ix_containers_tenant_status", "tenant_id", "status"),
        Index("ix_containers_tenant_created", "tenant_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    openai_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tenant_accounts.id", ondelete="CASCADE"), nullable=False
    )
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    memory_limit: Mapped[str] = mapped_column(String(8), nullable=False, default="1g")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    expires_after: Mapped[dict[str, object] | None] = mapped_column(JSONBCompat, nullable=True)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONBCompat, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, onupdate=UTC_NOW, nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    agent_bindings: Mapped[list[AgentContainer]] = relationship(
        "AgentContainer",
        back_populates="container",
        cascade="all, delete-orphan",
    )


class AgentContainer(Base):
    """Explicit binding of an agent key to a container within a tenant."""

    __tablename__ = "agent_containers"
    __table_args__ = (sa.PrimaryKeyConstraint("agent_key", "container_id", "tenant_id"),)

    agent_key: Mapped[str] = mapped_column(String(64), nullable=False)
    container_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("containers.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tenant_accounts.id", ondelete="CASCADE"), nullable=False
    )

    container: Mapped[Container] = relationship(back_populates="agent_bindings")


__all__ = ["Container", "AgentContainer"]
