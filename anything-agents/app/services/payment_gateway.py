"""Payment gateway abstraction for integrating with Stripe or other providers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


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


class PaymentGateway(Protocol):
    """Interface for subscription lifecycle interactions with a payment provider."""

    async def start_subscription(
        self,
        *,
        tenant_id: str,
        plan_code: str,
        billing_email: str | None,
        auto_renew: bool,
        seat_count: int | None,
    ) -> SubscriptionProvisionResult:
        ...

    async def update_subscription(
        self,
        subscription_id: str,
        *,
        auto_renew: bool | None = None,
        seat_count: int | None = None,
        billing_email: str | None = None,
    ) -> None:
        ...

    async def cancel_subscription(
        self,
        subscription_id: str,
        *,
        cancel_at_period_end: bool,
    ) -> None:
        ...

    async def record_usage(
        self,
        subscription_id: str,
        *,
        feature_key: str,
        quantity: int,
        idempotency_key: str | None,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> None:
        ...


class StripeGateway(PaymentGateway):
    """Stripe adapter placeholder; implements no-op logic until configured."""

    processor_name = "stripe"

    async def start_subscription(
        self,
        *,
        tenant_id: str,
        plan_code: str,
        billing_email: str | None,
        auto_renew: bool,
        seat_count: int | None,
    ) -> SubscriptionProvisionResult:
        # TODO: Integrate with stripe.Subscription create/checkout session.
        now = datetime.now(timezone.utc)
        return SubscriptionProvisionResult(
            processor=self.processor_name,
            customer_id=f"mock-customer-{tenant_id}",
            subscription_id=f"mock-subscription-{tenant_id}",
            starts_at=now,
            current_period_start=now,
            current_period_end=now,
            metadata={"plan_code": plan_code, "auto_renew": str(auto_renew)},
        )

    async def cancel_subscription(
        self,
        subscription_id: str,
        *,
        cancel_at_period_end: bool,
    ) -> None:
        # TODO: Call stripe.Subscription.modify(..., cancel_at_period_end=...)
        return None

    async def update_subscription(
        self,
        subscription_id: str,
        *,
        auto_renew: bool | None = None,
        seat_count: int | None = None,
        billing_email: str | None = None,
    ) -> None:
        # TODO: Call stripe.Subscription.modify for updates.
        return None

    async def record_usage(
        self,
        subscription_id: str,
        *,
        feature_key: str,
        quantity: int,
        idempotency_key: str | None,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> None:
        # TODO: Call stripe.SubscriptionItem.create_usage_record(...)
        return None


stripe_gateway = StripeGateway()
