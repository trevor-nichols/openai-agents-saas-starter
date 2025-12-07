"""SQLAlchemy ORM models for durable conversation storage."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import UTC_NOW, Base, uuid_pk
from app.infrastructure.persistence.types import JSONBCompat


# SQLite test environment cannot compile PostgreSQL computed expressions; suppress them there.
@compiles(Computed, "sqlite")  # pragma: no cover - dialect-specific DDL shim
def _sqlite_omit_computed(element, compiler, **kwargs):
    return ""

if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from app.infrastructure.persistence.auth.models import (
        TenantUserMembership,
        UserAccount,
    )
    from app.infrastructure.persistence.billing.models import TenantSubscription
    from app.infrastructure.persistence.tenants.models import TenantSettingsModel


class TenantAccount(Base):
    """Represents a customer tenant in a multi-tenant deployment."""

    __tablename__ = "tenant_accounts"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )

    memberships: Mapped[list[TenantUserMembership]] = relationship(
        "TenantUserMembership",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    users: Mapped[list[UserAccount]] = relationship(
        "UserAccount",
        secondary="tenant_user_memberships",
        back_populates="tenants",
        viewonly=True,
    )
    subscriptions: Mapped[list[TenantSubscription]] = relationship(
        "TenantSubscription",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    conversations: Mapped[list[AgentConversation]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
    settings: Mapped[TenantSettingsModel | None] = relationship(
        "TenantSettingsModel",
        back_populates="tenant",
        cascade="all, delete-orphan",
        uselist=False,
        single_parent=True,
    )


class AgentConversation(Base):
    """High-level thread for agent conversations."""

    __tablename__ = "agent_conversations"
    __table_args__ = (
        Index("ix_agent_conversations_tenant_updated", "tenant_id", "updated_at"),
        Index("ix_agent_conversations_tenant_status", "tenant_id", "status"),
        UniqueConstraint("conversation_key", name="uq_agent_conversations_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    conversation_key: Mapped[str] = mapped_column(String(255), nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenant_accounts.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    agent_entrypoint: Mapped[str] = mapped_column(String(64), nullable=False)
    active_agent: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default="active", nullable=False)
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens_prompt: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens_completion: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reasoning_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    provider: Mapped[str | None] = mapped_column(String(32))
    provider_conversation_id: Mapped[str | None] = mapped_column(String(128), unique=True)
    handoff_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_channel: Mapped[str | None] = mapped_column(String(32))
    topic_hint: Mapped[str | None] = mapped_column(String(256))
    display_name: Mapped[str | None] = mapped_column(String(128))
    title_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    memory_strategy: Mapped[str | None] = mapped_column(String(16))
    memory_max_turns: Mapped[int | None] = mapped_column(Integer)
    memory_keep_last_turns: Mapped[int | None] = mapped_column(Integer)
    memory_compact_trigger_turns: Mapped[int | None] = mapped_column(Integer)
    memory_compact_keep: Mapped[int | None] = mapped_column(Integer)
    memory_clear_tool_inputs: Mapped[bool | None] = mapped_column(nullable=True)
    memory_injection: Mapped[bool | None] = mapped_column(nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_run_id: Mapped[str | None] = mapped_column(String(64))
    client_version: Mapped[str | None] = mapped_column(String(32))
    sdk_session_id: Mapped[str | None] = mapped_column(String(255))
    session_cursor: Mapped[str | None] = mapped_column(String(128))
    last_session_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )

    tenant: Mapped[TenantAccount] = relationship(back_populates="conversations")
    user: Mapped[UserAccount | None] = relationship(back_populates="conversations")
    messages: Mapped[list[AgentMessage]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AgentMessage.position",
    )


class AgentMessage(Base):
    """Individual message within a conversation."""

    __tablename__ = "agent_messages"
    __table_args__ = (
        UniqueConstraint(
            "conversation_id",
            "position",
            name="uq_agent_messages_conversation_position",
        ),
        Index(
            "ix_agent_messages_conversation_created",
            "conversation_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agent_conversations.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    agent_type: Mapped[str | None] = mapped_column(String(64))
    content: Mapped[Any] = mapped_column(JSONBCompat, nullable=False)
    attachments: Mapped[list[dict[str, object]] | None] = mapped_column(
        JSONBCompat, nullable=True, default=list
    )
    tool_name: Mapped[str | None] = mapped_column(String(128))
    tool_call_id: Mapped[str | None] = mapped_column(String(64))
    token_count_prompt: Mapped[int | None] = mapped_column(Integer)
    token_count_completion: Mapped[int | None] = mapped_column(Integer)
    reasoning_tokens: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    content_checksum: Mapped[str | None] = mapped_column(String(32))
    run_id: Mapped[str | None] = mapped_column(String(64))
    text_tsv: Mapped[str | None] = mapped_column(
        TSVECTOR().with_variant(String(), "sqlite"),
        Computed(
            "to_tsvector('english', coalesce(content->>'text', ''))",
            persisted=True,
        ),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )

    conversation: Mapped[AgentConversation] = relationship(back_populates="messages")


class ConversationSummary(Base):
    """Cross-session summaries used for memory injection."""

    __tablename__ = "conversation_summaries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agent_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_key: Mapped[str | None] = mapped_column(String(64))
    summary_text: Mapped[str] = mapped_column(String)
    summary_model: Mapped[str | None] = mapped_column(String(64))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )


class AgentRunEvent(Base):
    """Structured event log entry mirroring SDK run items."""

    __tablename__ = "agent_run_events"
    __table_args__ = (
        UniqueConstraint("conversation_id", "sequence_no", name="uq_agent_run_events_seq"),
        Index("ix_agent_run_events_conv_seq", "conversation_id", "sequence_no"),
        Index("ix_agent_run_events_toolcall", "tool_call_id"),
        Index(
            "ix_agent_run_events_conv_type_seq",
            "conversation_id",
            "run_item_type",
            "sequence_no",
        ),
        Index("ix_agent_run_events_workflow_run", "workflow_run_id"),
        Index("ix_agent_run_events_workflow_run_seq", "workflow_run_id", "sequence_no"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agent_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    workflow_run_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("workflow_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    response_id: Mapped[str | None] = mapped_column(String(128))
    run_item_type: Mapped[str] = mapped_column(String(64), nullable=False)
    run_item_name: Mapped[str | None] = mapped_column(String(128))
    role: Mapped[str | None] = mapped_column(String(16))
    agent: Mapped[str | None] = mapped_column(String(64))
    tool_call_id: Mapped[str | None] = mapped_column(String(128))
    tool_name: Mapped[str | None] = mapped_column(String(128))
    model: Mapped[str | None] = mapped_column(String(64))
    content_text: Mapped[str | None] = mapped_column(String)
    reasoning_text: Mapped[str | None] = mapped_column(String)
    call_arguments: Mapped[dict[str, object] | None] = mapped_column(JSONBCompat)
    call_output: Mapped[dict[str, object] | None] = mapped_column(JSONBCompat)
    attachments: Mapped[list[dict[str, object]] | None] = mapped_column(JSONBCompat)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )


__all__ = [
    "Base",
    "TenantAccount",
    "AgentConversation",
    "AgentMessage",
    "AgentRunEvent",
    "ConversationSummary",
]
