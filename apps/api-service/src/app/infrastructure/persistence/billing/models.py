"""SQLAlchemy ORM models for the billing bounded context."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import INT_PK_TYPE, UTC_NOW, Base, uuid_pk
from app.infrastructure.persistence.types import JSONBCompat

if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from app.infrastructure.persistence.tenants.models import TenantAccount


class BillingPlan(Base):
    """Catalog of available billing plans."""

    __tablename__ = "billing_plans"
    __table_args__ = (UniqueConstraint("code", name="uq_billing_plans_code"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    interval: Mapped[str] = mapped_column(String(16), default="monthly", nullable=False)
    interval_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    trial_days: Mapped[int | None] = mapped_column(Integer)
    seat_included: Mapped[int | None] = mapped_column(Integer)
    feature_toggles: Mapped[dict[str, Any] | None] = mapped_column(JSONBCompat)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )

    features: Mapped[list[PlanFeature]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[list[TenantSubscription]] = relationship(back_populates="plan")


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

    id: Mapped[int] = mapped_column(INT_PK_TYPE, primary_key=True, autoincrement=True)
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

    plan: Mapped[BillingPlan] = relationship(back_populates="features")


class TenantSubscription(Base):
    """Subscription status for a tenant."""

    __tablename__ = "tenant_subscriptions"
    __table_args__ = (Index("ix_tenant_subscriptions_tenant_status", "tenant_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
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
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONBCompat)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=UTC_NOW, nullable=False
    )

    tenant: Mapped[TenantAccount] = relationship("TenantAccount")
    plan: Mapped[BillingPlan] = relationship(back_populates="subscriptions")
    invoices: Mapped[list[SubscriptionInvoice]] = relationship(
        back_populates="subscription",
        cascade="all, delete-orphan",
    )
    usage_records: Mapped[list[SubscriptionUsage]] = relationship(
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

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
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

    subscription: Mapped[TenantSubscription] = relationship(back_populates="invoices")


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

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
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

    subscription: Mapped[TenantSubscription] = relationship(back_populates="usage_records")


__all__ = [
    "BillingPlan",
    "PlanFeature",
    "TenantSubscription",
    "SubscriptionInvoice",
    "SubscriptionUsage",
]
