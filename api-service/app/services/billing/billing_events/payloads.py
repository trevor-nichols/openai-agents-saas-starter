"""Dataclasses for billing event payload structures."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class BillingEventSubscription:
    plan_code: str
    status: str
    seat_count: int | None
    auto_renew: bool
    current_period_start: str | None
    current_period_end: str | None
    trial_ends_at: str | None
    cancel_at: str | None


@dataclass(slots=True)
class BillingEventInvoice:
    invoice_id: str
    status: str
    amount_due_cents: int
    currency: str
    billing_reason: str | None
    hosted_invoice_url: str | None
    collection_method: str | None
    period_start: str | None
    period_end: str | None


@dataclass(slots=True)
class BillingEventUsage:
    feature_key: str
    quantity: int
    period_start: str | None
    period_end: str | None
    amount_cents: int | None


@dataclass(slots=True)
class BillingEventPayload:
    tenant_id: str
    event_type: str
    stripe_event_id: str
    occurred_at: str
    summary: str | None
    status: str
    subscription: BillingEventSubscription | None = None
    invoice: BillingEventInvoice | None = None
    usage: list[BillingEventUsage] = field(default_factory=list)
