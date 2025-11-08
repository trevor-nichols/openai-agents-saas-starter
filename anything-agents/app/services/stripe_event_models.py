"""Shared dataclasses for Stripe webhook dispatch + billing streams."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass(slots=True)
class UsageDelta:
    feature_key: str
    quantity: int
    period_start: datetime | None
    period_end: datetime | None
    idempotency_key: str | None = None
    amount_cents: int | None = None


@dataclass(slots=True)
class SubscriptionSnapshotView:
    tenant_id: str
    plan_code: str
    status: str
    auto_renew: bool
    seat_count: int | None
    current_period_start: datetime | None
    current_period_end: datetime | None
    trial_ends_at: datetime | None
    cancel_at: datetime | None


@dataclass(slots=True)
class InvoiceSnapshotView:
    tenant_id: str
    invoice_id: str
    status: str
    amount_due_cents: int
    currency: str
    billing_reason: str | None
    hosted_invoice_url: str | None
    collection_method: str | None
    period_start: datetime | None
    period_end: datetime | None


@dataclass(slots=True)
class DispatchBroadcastContext:
    tenant_id: str
    event_type: str
    summary: str | None
    status: str | None
    subscription: SubscriptionSnapshotView | None = None
    invoice: InvoiceSnapshotView | None = None
    usage: List[UsageDelta] = field(default_factory=list)


@dataclass(slots=True)
class DispatchResult:
    processed_at: datetime | None
    broadcast: DispatchBroadcastContext | None = None


__all__ = [
    "DispatchBroadcastContext",
    "DispatchResult",
    "InvoiceSnapshotView",
    "SubscriptionSnapshotView",
    "UsageDelta",
]
