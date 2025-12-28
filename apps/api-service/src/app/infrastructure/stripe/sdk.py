"""Thin wrappers around the Stripe SDK calls."""

from __future__ import annotations

from typing import Any

import stripe

from app.infrastructure.stripe.types import (
    SubscriptionCreateParams,
    SubscriptionScheduleCreateParams,
    UsageRecordPayload,
    call_create_usage_record,
    call_subscription_create,
    call_subscription_delete,
    call_subscription_modify,
    call_subscription_schedule_create,
    call_subscription_schedule_modify,
    call_subscription_schedule_release,
    call_subscription_schedule_retrieve,
)

SUBSCRIPTION_EXPAND_FIELDS = ["items.data.price"]


def configure_stripe_sdk(api_key: str) -> None:
    stripe.api_key = api_key
    stripe.max_network_retries = 0


def create_customer(payload: dict[str, Any]) -> Any:
    return stripe.Customer.create(**payload)


def modify_customer(customer_id: str, **params: Any) -> Any:
    return stripe.Customer.modify(customer_id, **params)


def retrieve_customer(customer_id: str) -> Any:
    return stripe.Customer.retrieve(customer_id)


def create_subscription(payload: SubscriptionCreateParams) -> Any:
    return call_subscription_create(payload)


def retrieve_subscription(subscription_id: str) -> Any:
    return stripe.Subscription.retrieve(subscription_id, expand=SUBSCRIPTION_EXPAND_FIELDS)


def modify_subscription(subscription_id: str, params: dict[str, Any]) -> Any:
    return call_subscription_modify(subscription_id, params)


def delete_subscription(subscription_id: str, params: dict[str, Any]) -> Any:
    return call_subscription_delete(subscription_id, params)


def create_subscription_schedule(payload: SubscriptionScheduleCreateParams) -> Any:
    return call_subscription_schedule_create(payload)


def retrieve_subscription_schedule(schedule_id: str) -> Any:
    return call_subscription_schedule_retrieve(schedule_id)


def modify_subscription_schedule(schedule_id: str, params: dict[str, Any]) -> Any:
    return call_subscription_schedule_modify(schedule_id, params)


def release_subscription_schedule(schedule_id: str) -> Any:
    return call_subscription_schedule_release(schedule_id)


def create_usage_record(payload: UsageRecordPayload) -> Any:
    return call_create_usage_record(payload)


def create_billing_portal_session(customer_id: str, return_url: str) -> Any:
    return stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )


def list_payment_methods(customer_id: str) -> Any:
    return stripe.PaymentMethod.list(customer=customer_id, type="card")


def retrieve_payment_method(payment_method_id: str) -> Any:
    return stripe.PaymentMethod.retrieve(payment_method_id)


def create_setup_intent(customer_id: str) -> Any:
    return stripe.SetupIntent.create(
        customer=customer_id,
        payment_method_types=["card"],
        usage="off_session",
    )


def set_default_payment_method(customer_id: str, payment_method_id: str) -> Any:
    return stripe.Customer.modify(
        customer_id,
        invoice_settings={"default_payment_method": payment_method_id},
    )


def detach_payment_method(payment_method_id: str) -> Any:
    return stripe.PaymentMethod.detach(payment_method_id)


def preview_upcoming_invoice(params: dict[str, Any]) -> Any:
    return stripe.Invoice.upcoming(**params)


__all__ = [
    "SUBSCRIPTION_EXPAND_FIELDS",
    "configure_stripe_sdk",
    "create_billing_portal_session",
    "create_customer",
    "create_setup_intent",
    "create_subscription",
    "create_subscription_schedule",
    "create_usage_record",
    "delete_subscription",
    "detach_payment_method",
    "list_payment_methods",
    "modify_customer",
    "modify_subscription",
    "modify_subscription_schedule",
    "preview_upcoming_invoice",
    "release_subscription_schedule",
    "retrieve_customer",
    "retrieve_payment_method",
    "retrieve_subscription",
    "retrieve_subscription_schedule",
    "set_default_payment_method",
]
