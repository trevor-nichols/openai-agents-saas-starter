"""Stripe client protocol for gateway injection/testing."""

from __future__ import annotations

from typing import Protocol

from app.infrastructure.stripe import (
    StripeCustomer,
    StripePaymentMethodDetail,
    StripePaymentMethodList,
    StripePortalSession,
    StripeSetupIntent,
    StripeSubscription,
    StripeSubscriptionSchedule,
    StripeUpcomingInvoice,
    StripeUsageRecord,
)
from app.infrastructure.stripe.types import SubscriptionSchedulePhasePayload


class StripeGatewayClient(Protocol):
    async def create_customer(self, *, email: str | None, tenant_id: str) -> StripeCustomer: ...

    async def create_subscription(
        self,
        *,
        customer_id: str,
        price_id: str,
        quantity: int,
        auto_renew: bool,
        trial_period_days: int | None = None,
        metadata: dict[str, str] | None = None,
    ) -> StripeSubscription: ...

    async def retrieve_subscription(self, subscription_id: str) -> StripeSubscription: ...

    async def modify_subscription(
        self,
        subscription: StripeSubscription,
        *,
        auto_renew: bool | None = None,
        seat_count: int | None = None,
        price_id: str | None = None,
        metadata: dict[str, str] | None = None,
        proration_behavior: str | None = None,
    ) -> StripeSubscription: ...

    async def create_subscription_schedule_from_subscription(
        self,
        subscription_id: str,
        *,
        end_behavior: str = "release",
    ) -> StripeSubscriptionSchedule: ...

    async def retrieve_subscription_schedule(
        self, schedule_id: str
    ) -> StripeSubscriptionSchedule: ...

    async def update_subscription_schedule(
        self,
        schedule_id: str,
        *,
        phases: list[SubscriptionSchedulePhasePayload],
        end_behavior: str | None = None,
        proration_behavior: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> StripeSubscriptionSchedule: ...

    async def release_subscription_schedule(
        self, schedule_id: str
    ) -> StripeSubscriptionSchedule: ...

    async def cancel_subscription(
        self, subscription_id: str, *, cancel_at_period_end: bool
    ) -> StripeSubscription: ...

    async def update_customer_email(self, customer_id: str, email: str) -> StripeCustomer: ...

    async def create_usage_record(
        self,
        subscription_item_id: str,
        *,
        quantity: int,
        timestamp: int,
        idempotency_key: str,
        feature_key: str,
    ) -> StripeUsageRecord: ...

    async def create_billing_portal_session(
        self, *, customer_id: str, return_url: str
    ) -> StripePortalSession: ...

    async def list_payment_methods(self, customer_id: str) -> StripePaymentMethodList: ...

    async def retrieve_payment_method(
        self, payment_method_id: str
    ) -> StripePaymentMethodDetail: ...

    async def create_setup_intent(self, customer_id: str) -> StripeSetupIntent: ...

    async def set_default_payment_method(
        self, *, customer_id: str, payment_method_id: str
    ) -> None: ...

    async def detach_payment_method(self, payment_method_id: str) -> None: ...

    async def preview_upcoming_invoice(
        self,
        *,
        customer_id: str,
        subscription_id: str,
        subscription_item_id: str | None,
        seat_count: int | None,
        proration_behavior: str | None = None,
    ) -> StripeUpcomingInvoice: ...


__all__ = ["StripeGatewayClient"]
