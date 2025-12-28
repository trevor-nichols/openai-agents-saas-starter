"""Stripe gateway helpers for common validation and timestamp handling."""

from __future__ import annotations

from datetime import UTC, datetime

from app.infrastructure.stripe import StripeSubscription, StripeSubscriptionItem
from app.services.billing.payment_gateway import PaymentGatewayError


def ensure_primary_item(
    subscription: StripeSubscription, *, message: str, error_code: str
) -> StripeSubscriptionItem:
    item = subscription.primary_item
    if item is None:
        raise PaymentGatewayError(message, code=error_code)
    return item


def resolve_quantity(item: StripeSubscriptionItem, seat_count: int | None) -> int:
    if seat_count is not None:
        return seat_count
    return item.quantity or 1


def require_period_start(subscription: StripeSubscription) -> datetime:
    if subscription.current_period_start is None:
        raise PaymentGatewayError(
            "Stripe subscription is missing a billing period start.",
            code="missing_period_start",
        )
    return subscription.current_period_start


def require_period_end(subscription: StripeSubscription) -> datetime:
    if subscription.current_period_end is None:
        raise PaymentGatewayError(
            "Stripe subscription is missing a billing period end.",
            code="missing_period_end",
        )
    return subscription.current_period_end


def to_utc_timestamp(value: datetime | None) -> int:
    target = value or datetime.now(UTC)
    if target.tzinfo is None:
        target = target.replace(tzinfo=UTC)
    else:
        target = target.astimezone(UTC)
    return int(target.timestamp())


def usage_timestamp(*, period_end: datetime | None, period_start: datetime | None) -> int:
    return to_utc_timestamp(period_end or period_start)


__all__ = [
    "ensure_primary_item",
    "require_period_end",
    "require_period_start",
    "resolve_quantity",
    "to_utc_timestamp",
    "usage_timestamp",
]
