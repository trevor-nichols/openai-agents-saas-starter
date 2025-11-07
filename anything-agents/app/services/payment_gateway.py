"""Payment gateway abstraction for integrating with Stripe or other providers."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol, Callable
from uuid import uuid4

from app.core.config import Settings, get_settings
from app.infrastructure.stripe import StripeClient

logger = logging.getLogger("anything-agents.services.payment_gateway")


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


class PaymentGatewayError(RuntimeError):
    """Raised when the payment provider returns a fatal error."""

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code


class StripeGateway(PaymentGateway):
    """Stripe adapter leveraging the typed Stripe client."""

    processor_name = "stripe"

    def __init__(
        self,
        client: StripeClient | None = None,
        settings_factory: Callable[[], Settings] | None = None,
    ) -> None:
        self._client = client
        self._settings_factory = settings_factory or get_settings

    async def start_subscription(
        self,
        *,
        tenant_id: str,
        plan_code: str,
        billing_email: str | None,
        auto_renew: bool,
        seat_count: int | None,
    ) -> SubscriptionProvisionResult:
        client = self._get_client()
        price_id = self._resolve_price_id(plan_code)
        quantity = seat_count or 1

        logger.info(
            "Provisioning Stripe subscription",
            extra={"tenant_id": tenant_id, "plan_code": plan_code, "quantity": quantity},
        )

        customer = await client.create_customer(email=billing_email, tenant_id=tenant_id)
        subscription = await client.create_subscription(
            customer_id=customer.id,
            price_id=price_id,
            quantity=quantity,
            auto_renew=auto_renew,
            metadata={"tenant_id": tenant_id, "plan_code": plan_code},
        )

        return SubscriptionProvisionResult(
            processor=self.processor_name,
            customer_id=customer.id,
            subscription_id=subscription.id,
            starts_at=subscription.current_period_start or datetime.now(timezone.utc),
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            trial_ends_at=subscription.trial_end,
            metadata={
                "stripe_price_id": price_id,
                "stripe_subscription_item_id": (subscription.primary_item.id if subscription.primary_item else ""),
            },
        )

    async def cancel_subscription(
        self,
        subscription_id: str,
        *,
        cancel_at_period_end: bool,
    ) -> None:
        client = self._get_client()
        logger.info(
            "Canceling Stripe subscription",
            extra={"subscription_id": subscription_id, "cancel_at_period_end": cancel_at_period_end},
        )
        await client.cancel_subscription(subscription_id, cancel_at_period_end=cancel_at_period_end)

    async def update_subscription(
        self,
        subscription_id: str,
        *,
        auto_renew: bool | None = None,
        seat_count: int | None = None,
        billing_email: str | None = None,
    ) -> None:
        if auto_renew is None and seat_count is None and billing_email is None:
            return None

        client = self._get_client()
        subscription = await client.retrieve_subscription(subscription_id)
        logger.info(
            "Updating Stripe subscription",
            extra={
                "subscription_id": subscription_id,
                "auto_renew": auto_renew,
                "seat_count": seat_count,
            },
        )
        await client.modify_subscription(
            subscription,
            auto_renew=auto_renew,
            seat_count=seat_count,
        )
        if billing_email:
            await client.update_customer_email(subscription.customer_id, billing_email)

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
        client = self._get_client()
        subscription = await client.retrieve_subscription(subscription_id)
        item = subscription.primary_item
        if item is None:
            raise PaymentGatewayError("Stripe subscription has no metered items for usage recording.")

        timestamp = _usage_timestamp(period_end=period_end, period_start=period_start)
        key = idempotency_key or f"usage-{subscription_id}-{timestamp}-{uuid4()}"
        logger.info(
            "Recording Stripe usage",
            extra={
                "subscription_id": subscription_id,
                "feature": feature_key,
                "quantity": quantity,
                "idempotency_key": key,
            },
        )
        await client.create_usage_record(
            item.id,
            quantity=quantity,
            timestamp=timestamp,
            idempotency_key=key,
            feature_key=feature_key,
        )

    def _get_client(self) -> StripeClient:
        if self._client is not None:
            return self._client
        settings = self._settings_factory()
        api_key = settings.stripe_secret_key
        if not api_key:
            raise PaymentGatewayError("STRIPE_SECRET_KEY is not configured.")
        self._client = StripeClient(api_key=api_key)
        return self._client

    def _resolve_price_id(self, plan_code: str) -> str:
        settings = self._settings_factory()
        mapping = settings.stripe_product_price_map or {}
        price_id = mapping.get(plan_code)
        if not price_id:
            raise PaymentGatewayError(f"No Stripe price configured for plan '{plan_code}'.")
        return price_id


def _usage_timestamp(*, period_end: datetime | None, period_start: datetime | None) -> int:
    target = period_end or period_start or datetime.now(timezone.utc)
    if target.tzinfo is None:
        target = target.replace(tzinfo=timezone.utc)
    else:
        target = target.astimezone(timezone.utc)
    return int(target.timestamp())


stripe_gateway = StripeGateway()
