"""Typing helpers and thin wrappers around the dynamic Stripe SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict, cast

import stripe


class SubscriptionItemPayload(TypedDict):
    """Subset of subscription item fields we populate when creating subscriptions."""

    price: str
    quantity: int


class SubscriptionCreateParams(TypedDict, total=False):
    """Shape of the payload passed to stripe.Subscription.create."""

    customer: str
    items: list[SubscriptionItemPayload]
    metadata: dict[str, str]
    expand: list[str]
    cancel_at_period_end: bool
    trial_period_days: int


class SubscriptionModifyItemPayload(TypedDict, total=False):
    """Mutation payload for subscription items."""

    id: str
    quantity: int


class SubscriptionModifyParams(TypedDict, total=False):
    """Allowed parameters when modifying an existing subscription."""

    cancel_at_period_end: bool
    items: list[SubscriptionModifyItemPayload]
    expand: list[str]


class UsageRecordPayload(TypedDict):
    """Fields required when creating usage records."""

    subscription_item_id: str
    quantity: int
    timestamp: int
    idempotency_key: str
    feature_key: str


if TYPE_CHECKING:

    class StripeAPIConnectionError(Exception):
        ...

    class StripeAPIError(Exception):
        ...

    class StripeRateLimitError(Exception):
        ...

    class StripeIdempotencyError(Exception):
        ...

else:
    _stripe_error_ns = getattr(stripe, "error", None)

    def _resolve_error(name: str) -> type[Exception]:
        candidate = getattr(_stripe_error_ns, name, None) if _stripe_error_ns else None
        if isinstance(candidate, type):
            return cast(type[Exception], candidate)
        return Exception

    StripeAPIConnectionError = _resolve_error("APIConnectionError")
    StripeAPIError = _resolve_error("APIError")
    StripeRateLimitError = _resolve_error("RateLimitError")
    StripeIdempotencyError = _resolve_error("IdempotencyError")


RETRYABLE_ERRORS: tuple[type[Exception], ...] = (
    StripeAPIConnectionError,
    StripeAPIError,
    StripeRateLimitError,
    StripeIdempotencyError,
)


def call_subscription_delete(subscription_id: str, params: dict[str, Any]) -> Any:
    """Invoke stripe.Subscription.delete with loose typing."""

    subscription_api = cast(Any, stripe.Subscription)
    return subscription_api.delete(subscription_id, **params)


def call_subscription_create(payload: SubscriptionCreateParams) -> Any:
    """Invoke stripe.Subscription.create with well-typed payloads."""

    subscription_api = cast(Any, stripe.Subscription)
    return subscription_api.create(**payload)


def call_subscription_modify(
    subscription_id: str, params: dict[str, Any]
) -> Any:
    """Invoke stripe.Subscription.modify with typed params."""

    subscription_api = cast(Any, stripe.Subscription)
    return subscription_api.modify(subscription_id, **params)


def call_create_usage_record(payload: UsageRecordPayload) -> Any:
    """Invoke stripe.SubscriptionItem.create_usage_record with custom metadata."""

    subscription_item = cast(Any, stripe.SubscriptionItem)
    return subscription_item.create_usage_record(
        payload["subscription_item_id"],
        quantity=payload["quantity"],
        timestamp=payload["timestamp"],
        action="increment",
        idempotency_key=payload["idempotency_key"],
        metadata={"feature": payload["feature_key"]},
    )
