"""SQLAlchemy ORM models for vector store metadata and file attachments."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import UTC_NOW, Base, uuid_pk
from app.infrastructure.persistence.types import JSONBCompat


class VectorStore(Base):
    __tablename__ = "vector_stores"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_vector_stores_tenant_name"),
        Index("ix_vector_stores_tenant_status", "tenant_id", "status"),
        Index("ix_vector_stores_tenant_created", "tenant_id", "created_at"),
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
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="creating")
    usage_bytes: Mapped[int] = mapped_column(default=0)
    expires_after: Mapped[dict[str, object] | None] = mapped_column(JSONBCompat, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONBCompat, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, onupdate=UTC_NOW, nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    files: Mapped[list[VectorStoreFile]] = relationship(
        "VectorStoreFile",
        back_populates="vector_store",
        cascade="all, delete-orphan",
    )
    agent_bindings: Mapped[list[AgentVectorStore]] = relationship(
        "AgentVectorStore",
        back_populates="vector_store",
        cascade="all, delete-orphan",
    )


class VectorStoreFile(Base):
    __tablename__ = "vector_store_files"
    __table_args__ = (
        UniqueConstraint(
            "vector_store_id", "openai_file_id", name="uq_vector_store_files_store_file"
        ),
        Index("ix_vector_store_files_store_status", "vector_store_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    openai_file_id: Mapped[str] = mapped_column(String(64), nullable=False)
    vector_store_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("vector_stores.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(256), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(128))
    size_bytes: Mapped[int | None] = mapped_column()
    usage_bytes: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="indexing")
    attributes_json: Mapped[dict[str, object]] = mapped_column(JSONBCompat, default=dict)
    chunking_json: Mapped[dict[str, object] | None] = mapped_column(JSONBCompat)
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, onupdate=UTC_NOW, nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    vector_store: Mapped[VectorStore] = relationship(back_populates="files")


class AgentVectorStore(Base):
    """Explicit binding of an agent key to a single vector store within a tenant."""

    __tablename__ = "agent_vector_stores"
    __table_args__ = (
        sa.PrimaryKeyConstraint("agent_key", "vector_store_id", "tenant_id"),
        sa.UniqueConstraint("tenant_id", "agent_key", name="uq_agent_vector_store_per_agent"),
    )

    agent_key: Mapped[str] = mapped_column(String(64), nullable=False)
    vector_store_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("vector_stores.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tenant_accounts.id", ondelete="CASCADE"), nullable=False
    )

    vector_store: Mapped[VectorStore] = relationship(back_populates="agent_bindings")


__all__ = ["VectorStore", "VectorStoreFile", "AgentVectorStore"]
