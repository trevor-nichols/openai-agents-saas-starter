"""SQLAlchemy ORM models for durable conversation and billing storage."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import Base, UTC_NOW, uuid_pk


class TenantAccount(Base):
    """Represents a customer tenant in a multi-tenant deployment."""

    __tablename__ = "tenant_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk
    )
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )

    users: Mapped[list["User"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[list["TenantSubscription"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["AgentConversation"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )


class User(Base):
    """Represents an authenticated user linked to a tenant."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "external_id", name="uq_users_tenant_external"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenant_accounts.id", ondelete="CASCADE"), nullable=False
    )
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )

    tenant: Mapped["TenantAccount"] = relationship(back_populates="users")
    conversations: Mapped[list["AgentConversation"]] = relationship(
        back_populates="user"
    )


class AgentConversation(Base):
    """High-level thread for agent conversations."""

    __tablename__ = "agent_conversations"
    __table_args__ = (
        Index("ix_agent_conversations_tenant_updated", "tenant_id", "updated_at"),
        Index("ix_agent_conversations_tenant_status", "tenant_id", "status"),
        UniqueConstraint("conversation_key", name="uq_agent_conversations_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk
    )
    conversation_key: Mapped[str] = mapped_column(String(255), nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenant_accounts.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    agent_entrypoint: Mapped[str] = mapped_column(String(64), nullable=False)
    active_agent: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default="active", nullable=False)
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens_prompt: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens_completion: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    reasoning_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    handoff_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_channel: Mapped[str | None] = mapped_column(String(32))
    topic_hint: Mapped[str | None] = mapped_column(String(256))
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_run_id: Mapped[str | None] = mapped_column(String(64))
    client_version: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )

    tenant: Mapped["TenantAccount"] = relationship(back_populates="conversations")
    user: Mapped["User | None"] = relationship(back_populates="conversations")
    messages: Mapped[list["AgentMessage"]] = relationship(
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
    content: Mapped[Any] = mapped_column(JSONB, nullable=False)
    tool_name: Mapped[str | None] = mapped_column(String(128))
    tool_call_id: Mapped[str | None] = mapped_column(String(64))
    token_count_prompt: Mapped[int | None] = mapped_column(Integer)
    token_count_completion: Mapped[int | None] = mapped_column(Integer)
    reasoning_tokens: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    content_checksum: Mapped[str | None] = mapped_column(String(32))
    run_id: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )

    conversation: Mapped["AgentConversation"] = relationship(back_populates="messages")


class BillingPlan(Base):
    """Catalog of available billing plans."""

    __tablename__ = "billing_plans"
    __table_args__ = (UniqueConstraint("code", name="uq_billing_plans_code"),)

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    interval: Mapped[str] = mapped_column(String(16), default="monthly", nullable=False)
    interval_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    trial_days: Mapped[int | None] = mapped_column(Integer)
    seat_included: Mapped[int | None] = mapped_column(Integer)
    feature_toggles: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )

    features: Mapped[list["PlanFeature"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[list["TenantSubscription"]] = relationship(
        back_populates="plan"
    )


class PlanFeature(Base):
    """Feature descriptors linked to a billing plan."""

    __tablename__ = "plan_features"
    __table_args__ = (
        UniqueConstraint(
            "plan_id",
            "feature_key",
            name="uq_plan_features_plan_feature",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("billing_plans.id", ondelete="CASCADE"), nullable=False
    )
    feature_key: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text)
    hard_limit: Mapped[int | None] = mapped_column(Integer)
    soft_limit: Mapped[int | None] = mapped_column(Integer)
    is_metered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )

    plan: Mapped["BillingPlan"] = relationship(back_populates="features")


class TenantSubscription(Base):
    """Subscription status for a tenant."""

    __tablename__ = "tenant_subscriptions"
    __table_args__ = (
        Index("ix_tenant_subscriptions_tenant_status", "tenant_id", "status"),
        UniqueConstraint(
            "tenant_id",
            "status",
            name="uq_tenant_subscriptions_active",
            deferrable=True,
            initially="IMMEDIATE",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenant_accounts.id", ondelete="CASCADE"), nullable=False
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("billing_plans.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(24), default="active", nullable=False)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    billing_email: Mapped[str | None] = mapped_column(String(256))
    processor: Mapped[str | None] = mapped_column(String(32))
    processor_customer_id: Mapped[str | None] = mapped_column(String(128))
    processor_subscription_id: Mapped[str | None] = mapped_column(String(128))
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    seat_count: Mapped[int | None] = mapped_column(Integer)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )

    tenant: Mapped["TenantAccount"] = relationship(back_populates="subscriptions")
    plan: Mapped["BillingPlan"] = relationship(back_populates="subscriptions")
    invoices: Mapped[list["SubscriptionInvoice"]] = relationship(
        back_populates="subscription",
        cascade="all, delete-orphan",
    )
    usage_records: Mapped[list["SubscriptionUsage"]] = relationship(
        back_populates="subscription",
        cascade="all, delete-orphan",
    )


class SubscriptionInvoice(Base):
    """Tracks billing periods and invoice metadata."""

    __tablename__ = "subscription_invoices"
    __table_args__ = (
        Index(
            "ix_subscription_invoices_subscription_period",
            "subscription_id",
            "period_start",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenant_subscriptions.id", ondelete="CASCADE"), nullable=False
    )
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="draft", nullable=False)
    external_invoice_id: Mapped[str | None] = mapped_column(String(128))
    hosted_invoice_url: Mapped[str | None] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )

    subscription: Mapped["TenantSubscription"] = relationship(back_populates="invoices")


class SubscriptionUsage(Base):
    """Metered usage records for subscriptions."""

    __tablename__ = "subscription_usage"
    __table_args__ = (
        UniqueConstraint(
            "subscription_id",
            "feature_key",
            "period_start",
            name="uq_subscription_usage_feature_period",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenant_subscriptions.id", ondelete="CASCADE"), nullable=False
    )
    feature_key: Mapped[str] = mapped_column(String(64), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )
    external_event_id: Mapped[str | None] = mapped_column(String(128))

    subscription: Mapped["TenantSubscription"] = relationship(
        back_populates="usage_records"
    )


__all__ = [
    "Base",
    "TenantAccount",
    "User",
    "AgentConversation",
    "AgentMessage",
    "BillingPlan",
    "PlanFeature",
    "TenantSubscription",
    "SubscriptionInvoice",
    "SubscriptionUsage",
]
