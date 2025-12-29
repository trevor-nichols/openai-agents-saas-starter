"""Service-level value objects for billing workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from app.domain.billing import TenantSubscription


class PlanChangeTiming(StrEnum):
    AUTO = "auto"
    IMMEDIATE = "immediate"
    PERIOD_END = "period_end"


@dataclass(slots=True)
class ProcessorSubscriptionSnapshot:
    tenant_id: str
    plan_code: str
    status: str
    auto_renew: bool
    starts_at: datetime | None
    current_period_start: datetime | None
    current_period_end: datetime | None
    trial_ends_at: datetime | None
    cancel_at: datetime | None
    seat_count: int | None
    billing_email: str | None
    processor_customer_id: str | None
    processor_subscription_id: str
    processor_schedule_id: str | None
    metadata: dict[str, str]


@dataclass(slots=True)
class ProcessorInvoiceLineSnapshot:
    feature_key: str
    quantity: int
    period_start: datetime | None
    period_end: datetime | None
    idempotency_key: str | None = None
    amount_cents: int | None = None


@dataclass(slots=True)
class ProcessorInvoiceSnapshot:
    tenant_id: str
    invoice_id: str
    status: str
    amount_due_cents: int
    currency: str
    period_start: datetime | None
    period_end: datetime | None
    hosted_invoice_url: str | None
    billing_reason: str | None
    collection_method: str | None
    description: str | None = None
    lines: list[ProcessorInvoiceLineSnapshot] = field(default_factory=list)


@dataclass(slots=True)
class PlanChangeResult:
    subscription: TenantSubscription
    target_plan_code: str
    effective_at: datetime | None
    seat_count: int | None
    timing: PlanChangeTiming


@dataclass(slots=True)
class UpcomingInvoiceLineSnapshot:
    description: str | None
    amount_cents: int
    currency: str | None
    quantity: int | None
    unit_amount_cents: int | None
    price_id: str | None


@dataclass(slots=True)
class UpcomingInvoicePreview:
    plan_code: str
    plan_name: str
    seat_count: int | None
    invoice_id: str | None
    amount_due_cents: int
    currency: str
    period_start: datetime | None
    period_end: datetime | None
    lines: list[UpcomingInvoiceLineSnapshot] = field(default_factory=list)


__all__ = [
    "PlanChangeResult",
    "PlanChangeTiming",
    "ProcessorInvoiceLineSnapshot",
    "ProcessorInvoiceSnapshot",
    "ProcessorSubscriptionSnapshot",
    "UpcomingInvoiceLineSnapshot",
    "UpcomingInvoicePreview",
]
