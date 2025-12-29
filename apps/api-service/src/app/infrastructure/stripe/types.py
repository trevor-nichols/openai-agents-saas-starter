"""Typing helpers and thin wrappers around the dynamic Stripe SDK."""

from __future__ import annotations

from typing import Any, TypedDict, cast

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
    price: str


class SubscriptionModifyParams(TypedDict, total=False):
    """Allowed parameters when modifying an existing subscription."""

    cancel_at_period_end: bool
    items: list[SubscriptionModifyItemPayload]
    expand: list[str]
    metadata: dict[str, str]
    proration_behavior: str


class SubscriptionScheduleItemPayload(TypedDict, total=False):
    price: str
    quantity: int


class SubscriptionSchedulePhasePayload(TypedDict, total=False):
    items: list[SubscriptionScheduleItemPayload]
    start_date: int
    end_date: int
    proration_behavior: str
    metadata: dict[str, str]


class SubscriptionScheduleCreateParams(TypedDict, total=False):
    from_subscription: str
    end_behavior: str


class SubscriptionScheduleModifyParams(TypedDict, total=False):
    phases: list[SubscriptionSchedulePhasePayload]
    end_behavior: str
    proration_behavior: str
    metadata: dict[str, str]


class UsageRecordPayload(TypedDict):
    """Fields required when creating usage records."""

    subscription_item_id: str
    quantity: int
    timestamp: int
    idempotency_key: str
    feature_key: str


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


def call_subscription_schedule_create(payload: SubscriptionScheduleCreateParams) -> Any:
    """Invoke stripe.SubscriptionSchedule.create with typed params."""

    schedule_api = cast(Any, stripe.SubscriptionSchedule)
    return schedule_api.create(**payload)


def call_subscription_schedule_modify(
    schedule_id: str, params: dict[str, Any]
) -> Any:
    """Invoke stripe.SubscriptionSchedule.modify with typed params."""

    schedule_api = cast(Any, stripe.SubscriptionSchedule)
    return schedule_api.modify(schedule_id, **params)


def call_subscription_schedule_release(
    schedule_id: str,
) -> Any:
    """Invoke stripe.SubscriptionSchedule.release."""

    schedule_api = cast(Any, stripe.SubscriptionSchedule)
    return schedule_api.release(schedule_id)


def call_subscription_schedule_retrieve(
    schedule_id: str,
) -> Any:
    """Invoke stripe.SubscriptionSchedule.retrieve."""

    schedule_api = cast(Any, stripe.SubscriptionSchedule)
    return schedule_api.retrieve(schedule_id)
