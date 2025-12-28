"""Stripe integration data models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class StripeCustomer:
    id: str
    email: str | None = None


@dataclass(slots=True)
class StripeSubscriptionItem:
    id: str
    price_id: str | None
    quantity: int | None


@dataclass(slots=True)
class StripeSubscription:
    id: str
    customer_id: str
    status: str
    cancel_at_period_end: bool
    current_period_start: datetime | None
    current_period_end: datetime | None
    trial_end: datetime | None
    items: list[StripeSubscriptionItem]
    schedule_id: str | None = None
    metadata: dict[str, str] | None = None

    @property
    def primary_item(self) -> StripeSubscriptionItem | None:
        return self.items[0] if self.items else None


@dataclass(slots=True)
class StripeSubscriptionSchedulePhase:
    start_date: datetime | None
    end_date: datetime | None
    items: list[StripeSubscriptionItem]
    proration_behavior: str | None = None


@dataclass(slots=True)
class StripeSubscriptionSchedule:
    id: str
    status: str
    subscription_id: str | None
    phases: list[StripeSubscriptionSchedulePhase]
    current_phase: StripeSubscriptionSchedulePhase | None = None
    metadata: dict[str, str] | None = None


@dataclass(slots=True)
class StripeUsageRecord:
    id: str
    subscription_item_id: str
    quantity: int
    timestamp: datetime


@dataclass(slots=True)
class StripePortalSession:
    url: str


@dataclass(slots=True)
class StripePaymentMethod:
    id: str
    brand: str | None
    last4: str | None
    exp_month: int | None
    exp_year: int | None


@dataclass(slots=True)
class StripePaymentMethodDetail:
    id: str
    customer_id: str | None = None


@dataclass(slots=True)
class StripePaymentMethodList:
    items: list[StripePaymentMethod]
    default_payment_method_id: str | None = None


@dataclass(slots=True)
class StripeSetupIntent:
    id: str
    client_secret: str | None


@dataclass(slots=True)
class StripeUpcomingInvoiceLine:
    description: str | None
    amount: int
    currency: str | None
    quantity: int | None
    unit_amount: int | None
    price_id: str | None


@dataclass(slots=True)
class StripeUpcomingInvoice:
    id: str | None
    amount_due: int
    currency: str
    period_start: datetime | None
    period_end: datetime | None
    lines: list[StripeUpcomingInvoiceLine]


__all__ = [
    "StripeCustomer",
    "StripePaymentMethod",
    "StripePaymentMethodDetail",
    "StripePaymentMethodList",
    "StripePortalSession",
    "StripeSetupIntent",
    "StripeSubscription",
    "StripeSubscriptionItem",
    "StripeSubscriptionSchedule",
    "StripeSubscriptionSchedulePhase",
    "StripeUpcomingInvoice",
    "StripeUpcomingInvoiceLine",
    "StripeUsageRecord",
]
