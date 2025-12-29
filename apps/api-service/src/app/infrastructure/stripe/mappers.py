"""Pure mapping helpers from Stripe SDK objects to local models."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from app.infrastructure.stripe.models import (
    StripePaymentMethod,
    StripeSubscription,
    StripeSubscriptionItem,
    StripeSubscriptionSchedule,
    StripeSubscriptionSchedulePhase,
    StripeUpcomingInvoiceLine,
)


def iter_items(items: Any) -> Iterable[Any]:
    data = getattr(items, "data", None)
    if isinstance(data, list):
        return data
    return []


def extract_default_payment_method_id(customer: Any) -> str | None:
    invoice_settings = getattr(customer, "invoice_settings", None)
    if isinstance(invoice_settings, dict):
        value = invoice_settings.get("default_payment_method")
    else:
        value = getattr(invoice_settings, "default_payment_method", None)
    if isinstance(value, dict):
        return value.get("id")
    return str(value) if value else None


def extract_payment_method_customer_id(method: Any) -> str | None:
    customer = getattr(method, "customer", None)
    if isinstance(customer, dict):
        value = customer.get("id")
    else:
        value = customer
    return str(value) if value else None


def extract_schedule_id(schedule: Any) -> str | None:
    if schedule is None:
        return None
    if isinstance(schedule, str):
        return schedule
    if isinstance(schedule, dict):
        return schedule.get("id")
    return getattr(schedule, "id", None)


def to_datetime(value: int | float | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromtimestamp(float(value), tz=UTC)


def to_subscription(subscription: Any) -> StripeSubscription:
    items = [to_subscription_item(item) for item in iter_items(subscription.items)]
    metadata = dict(getattr(subscription, "metadata", None) or {})
    return StripeSubscription(
        id=subscription.id,
        customer_id=subscription.customer,
        status=subscription.status,
        cancel_at_period_end=bool(subscription.cancel_at_period_end),
        current_period_start=to_datetime(getattr(subscription, "current_period_start", None)),
        current_period_end=to_datetime(getattr(subscription, "current_period_end", None)),
        trial_end=to_datetime(getattr(subscription, "trial_end", None)),
        items=items,
        schedule_id=extract_schedule_id(getattr(subscription, "schedule", None)),
        metadata=metadata,
    )


def to_subscription_item(item: Any) -> StripeSubscriptionItem:
    price = getattr(item, "price", None)
    price_id = getattr(price, "id", None) if price else None
    return StripeSubscriptionItem(
        id=item.id,
        price_id=price_id,
        quantity=getattr(item, "quantity", None),
    )


def to_schedule(schedule: Any) -> StripeSubscriptionSchedule:
    phases_data = getattr(schedule, "phases", None)
    phases: list[StripeSubscriptionSchedulePhase] = []
    if isinstance(phases_data, list):
        for phase in phases_data:
            if isinstance(phase, dict):
                items_raw = phase.get("items")
                start_raw = phase.get("start_date")
                end_raw = phase.get("end_date")
                proration = phase.get("proration_behavior")
            else:
                items_raw = getattr(phase, "items", None)
                start_raw = getattr(phase, "start_date", None)
                end_raw = getattr(phase, "end_date", None)
                proration = getattr(phase, "proration_behavior", None)

            items = [to_subscription_item(item) for item in iter_items(items_raw)]
            phases.append(
                StripeSubscriptionSchedulePhase(
                    start_date=to_datetime(start_raw),
                    end_date=to_datetime(end_raw),
                    items=items,
                    proration_behavior=proration,
                )
            )

    current = getattr(schedule, "current_phase", None)
    current_phase = None
    if isinstance(current, dict):
        current_phase = StripeSubscriptionSchedulePhase(
            start_date=to_datetime(current.get("start_date")),
            end_date=to_datetime(current.get("end_date")),
            items=[],
            proration_behavior=None,
        )

    subscription_id = getattr(schedule, "subscription", None)
    if isinstance(subscription_id, dict):
        subscription_id = subscription_id.get("id")

    return StripeSubscriptionSchedule(
        id=schedule.id,
        status=getattr(schedule, "status", "unknown"),
        subscription_id=subscription_id,
        phases=phases,
        current_phase=current_phase,
        metadata=dict(getattr(schedule, "metadata", None) or {}),
    )


def to_payment_method(method: Any) -> StripePaymentMethod:
    card = getattr(method, "card", None)
    brand = getattr(card, "brand", None) if card else None
    last4 = getattr(card, "last4", None) if card else None
    exp_month = getattr(card, "exp_month", None) if card else None
    exp_year = getattr(card, "exp_year", None) if card else None
    return StripePaymentMethod(
        id=method.id,
        brand=brand,
        last4=last4,
        exp_month=exp_month,
        exp_year=exp_year,
    )


def to_invoice_line(line: Any) -> StripeUpcomingInvoiceLine:
    price = getattr(line, "price", None)
    price_id = None
    unit_amount = None
    if price is not None:
        price_id = getattr(price, "id", None)
        unit_amount = getattr(price, "unit_amount", None)
    return StripeUpcomingInvoiceLine(
        description=getattr(line, "description", None),
        amount=int(getattr(line, "amount", 0) or 0),
        currency=getattr(line, "currency", None),
        quantity=getattr(line, "quantity", None),
        unit_amount=unit_amount,
        price_id=price_id,
    )


__all__ = [
    "extract_default_payment_method_id",
    "extract_payment_method_customer_id",
    "extract_schedule_id",
    "iter_items",
    "to_datetime",
    "to_invoice_line",
    "to_payment_method",
    "to_schedule",
    "to_subscription",
    "to_subscription_item",
]
