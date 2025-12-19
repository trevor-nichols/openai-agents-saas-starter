"""ORM models for agent assets catalog."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import UTC_NOW, Base, uuid_pk
from app.infrastructure.persistence.types import JSONBCompat


class AgentAsset(Base):
    __tablename__ = "agent_assets"
    __table_args__ = (
        UniqueConstraint("storage_object_id", name="uq_agent_assets_storage_object"),
        Index("ix_agent_assets_tenant_type_created", "tenant_id", "asset_type", "created_at"),
        Index("ix_agent_assets_conversation", "conversation_id"),
        Index("ix_agent_assets_message", "message_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenant_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    storage_object_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("storage_objects.id", ondelete="CASCADE"),
        nullable=False,
    )
    asset_type: Mapped[str] = mapped_column(String(16), nullable=False)
    source_tool: Mapped[str | None] = mapped_column(String(32))
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agent_conversations.id", ondelete="SET NULL"),
        nullable=True,
    )
    message_id: Mapped[int | None] = mapped_column(
        ForeignKey("agent_messages.id", ondelete="SET NULL"), nullable=True
    )
    tool_call_id: Mapped[str | None] = mapped_column(String(255))
    response_id: Mapped[str | None] = mapped_column(String(128))
    container_id: Mapped[str | None] = mapped_column(String(128))
    openai_file_id: Mapped[str | None] = mapped_column(String(128))
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONBCompat, default=dict)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, onupdate=UTC_NOW, nullable=False
    )


__all__ = ["AgentAsset"]
