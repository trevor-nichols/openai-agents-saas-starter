"""Value objects for payment gateway interactions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class SubscriptionProvisionResult:
    processor: str
    customer_id: str
    subscription_id: str
    starts_at: datetime
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    trial_ends_at: datetime | None = None
    metadata: dict[str, str] | None = None


@dataclass(slots=True)
class CustomerProvisionResult:
    processor: str
    customer_id: str
    billing_email: str | None = None


@dataclass(slots=True)
class PortalSessionResult:
    url: str


@dataclass(slots=True)
class PaymentMethodSummary:
    id: str
    brand: str | None
    last4: str | None
    exp_month: int | None
    exp_year: int | None
    is_default: bool = False


@dataclass(slots=True)
class SetupIntentResult:
    id: str
    client_secret: str | None


@dataclass(slots=True)
class UpcomingInvoiceLine:
    description: str | None
    amount_cents: int
    currency: str | None
    quantity: int | None
    unit_amount_cents: int | None
    price_id: str | None


@dataclass(slots=True)
class UpcomingInvoicePreviewResult:
    invoice_id: str | None
    amount_due_cents: int
    currency: str
    period_start: datetime | None
    period_end: datetime | None
    lines: list[UpcomingInvoiceLine]


@dataclass(slots=True)
class SubscriptionPlanSwapResult:
    price_id: str
    subscription_item_id: str | None
    current_period_start: datetime | None
    current_period_end: datetime | None
    quantity: int | None
    metadata: dict[str, str] | None = None


@dataclass(slots=True)
class SubscriptionPlanScheduleResult:
    schedule_id: str
    price_id: str
    current_period_start: datetime | None
    current_period_end: datetime | None
    quantity: int | None
    metadata: dict[str, str] | None = None


__all__ = [
    "CustomerProvisionResult",
    "PaymentMethodSummary",
    "PortalSessionResult",
    "SetupIntentResult",
    "SubscriptionPlanScheduleResult",
    "SubscriptionPlanSwapResult",
    "SubscriptionProvisionResult",
    "UpcomingInvoiceLine",
    "UpcomingInvoicePreviewResult",
]
