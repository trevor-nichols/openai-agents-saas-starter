"""Payment gateway abstraction for integrating with Stripe or other providers."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter
from typing import Protocol, TypeVar
from uuid import uuid4

from app.core.config import Settings, get_settings
from app.infrastructure.stripe import (
    StripeClient,
    StripeClientError,
    StripeCustomer,
    StripeSubscription,
    StripeUsageRecord,
)
from app.observability.metrics import observe_stripe_gateway_operation

logger = logging.getLogger("anything-agents.services.payment_gateway")

T = TypeVar("T")


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
    ) -> SubscriptionProvisionResult: ...

    async def update_subscription(
        self,
        subscription_id: str,
        *,
        auto_renew: bool | None = None,
        seat_count: int | None = None,
        billing_email: str | None = None,
    ) -> None: ...

    async def cancel_subscription(
        self,
        subscription_id: str,
        *,
        cancel_at_period_end: bool,
    ) -> None: ...

    async def record_usage(
        self,
        subscription_id: str,
        *,
        feature_key: str,
        quantity: int,
        idempotency_key: str | None,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> None: ...


class PaymentGatewayError(RuntimeError):
    """Raised when the payment provider returns a fatal error."""

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code


class StripeGatewayClient(Protocol):
    async def create_customer(self, *, email: str | None, tenant_id: str) -> StripeCustomer: ...

    async def create_subscription(
        self,
        *,
        customer_id: str,
        price_id: str,
        quantity: int,
        auto_renew: bool,
        metadata: dict[str, str] | None = None,
    ) -> StripeSubscription: ...

    async def retrieve_subscription(self, subscription_id: str) -> StripeSubscription: ...

    async def modify_subscription(
        self,
        subscription: StripeSubscription,
        *,
        auto_renew: bool | None = None,
        seat_count: int | None = None,
    ) -> StripeSubscription: ...

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


class StripeGateway(PaymentGateway):
    """Stripe adapter leveraging the typed Stripe client."""

    processor_name = "stripe"

    def __init__(
        self,
        client: StripeGatewayClient | None = None,
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
        quantity = seat_count or 1

        async def _action() -> SubscriptionProvisionResult:
            client = self._get_client()
            price_id = self._resolve_price_id(plan_code)

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
                starts_at=subscription.current_period_start or datetime.now(UTC),
                current_period_start=subscription.current_period_start,
                current_period_end=subscription.current_period_end,
                trial_ends_at=subscription.trial_end,
                metadata={
                    "stripe_price_id": price_id,
                    "stripe_subscription_item_id": (
                        subscription.primary_item.id if subscription.primary_item else ""
                    ),
                },
            )

        return await self._execute_operation(
            operation="start_subscription",
            plan_code=plan_code,
            tenant_id=tenant_id,
            subscription_id=None,
            context={
                "quantity": quantity,
                "seat_count": seat_count,
                "auto_renew": auto_renew,
                "has_billing_email": bool(billing_email),
            },
            action=_action,
        )

    async def cancel_subscription(
        self,
        subscription_id: str,
        *,
        cancel_at_period_end: bool,
    ) -> None:
        async def _action() -> None:
            client = self._get_client()
            await client.cancel_subscription(
                subscription_id, cancel_at_period_end=cancel_at_period_end
            )

        await self._execute_operation(
            operation="cancel_subscription",
            plan_code=None,
            tenant_id=None,
            subscription_id=subscription_id,
            context={"cancel_at_period_end": cancel_at_period_end},
            action=_action,
        )

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

        async def _action() -> None:
            client = self._get_client()
            subscription = await client.retrieve_subscription(subscription_id)
            await client.modify_subscription(
                subscription,
                auto_renew=auto_renew,
                seat_count=seat_count,
            )
            if billing_email:
                await client.update_customer_email(subscription.customer_id, billing_email)

        await self._execute_operation(
            operation="update_subscription",
            plan_code=None,
            tenant_id=None,
            subscription_id=subscription_id,
            context={
                "auto_renew": auto_renew,
                "seat_count": seat_count,
                "has_billing_email": bool(billing_email),
            },
            action=_action,
        )

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
        async def _action() -> None:
            client = self._get_client()
            subscription = await client.retrieve_subscription(subscription_id)
            item = subscription.primary_item
            if item is None:
                raise PaymentGatewayError(
                    "Stripe subscription has no metered items for usage recording.",
                    code="missing_metered_item",
                )

            timestamp = _usage_timestamp(period_end=period_end, period_start=period_start)
            key = idempotency_key or f"usage-{subscription_id}-{timestamp}-{uuid4()}"
            logger.info(
                "Preparing Stripe usage record",
                extra={
                    "stripe_gateway_operation": "record_usage",
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

        await self._execute_operation(
            operation="record_usage",
            plan_code=None,
            tenant_id=None,
            subscription_id=subscription_id,
            context={
                "feature": feature_key,
                "quantity": quantity,
                "has_idempotency_key": bool(idempotency_key),
            },
            action=_action,
        )

    def _get_client(self) -> StripeGatewayClient:
        if self._client is not None:
            return self._client
        settings = self._settings_factory()
        api_key = settings.stripe_secret_key
        if not api_key:
            raise PaymentGatewayError("STRIPE_SECRET_KEY is not configured.", code="config_missing")
        self._client = StripeClient(api_key=api_key)
        return self._client

    def _resolve_price_id(self, plan_code: str) -> str:
        settings = self._settings_factory()
        mapping = settings.stripe_product_price_map or {}
        price_id = mapping.get(plan_code)
        if not price_id:
            raise PaymentGatewayError(
                f"No Stripe price configured for plan '{plan_code}'.",
                code="price_mapping_missing",
            )
        return price_id

    async def _execute_operation(
        self,
        *,
        operation: str,
        plan_code: str | None,
        tenant_id: str | None,
        subscription_id: str | None,
        context: dict[str, object] | None,
        action: Callable[[], Awaitable[T]],
    ) -> T:
        base_context: dict[str, object] = {
            "stripe_gateway_operation": operation,
        }
        if plan_code:
            base_context["plan_code"] = plan_code
        if tenant_id:
            base_context["tenant_id"] = tenant_id
        if subscription_id:
            base_context["subscription_id"] = subscription_id
        if context:
            for key, value in context.items():
                if value is not None:
                    base_context[key] = value

        logger.info("Stripe gateway operation started", extra=base_context)
        start = perf_counter()

        try:
            result = await action()
        except PaymentGatewayError as exc:
            duration = perf_counter() - start
            observe_stripe_gateway_operation(
                operation=operation,
                plan_code=plan_code,
                result=exc.code or "error",
                duration_seconds=duration,
            )
            failure_context = {
                **base_context,
                "duration_ms": int(duration * 1000),
                "error": str(exc),
                "error_code": exc.code or "error",
            }
            logger.warning("Stripe gateway operation failed", extra=failure_context)
            raise
        except StripeClientError as exc:
            duration = perf_counter() - start
            error_code = exc.code or "stripe_error"
            observe_stripe_gateway_operation(
                operation=operation,
                plan_code=plan_code,
                result=error_code,
                duration_seconds=duration,
            )
            failure_context = {
                **base_context,
                "duration_ms": int(duration * 1000),
                "error": str(exc),
                "error_code": error_code,
            }
            logger.error("Stripe API error during gateway operation", extra=failure_context)
            raise PaymentGatewayError(
                f"Stripe error during {operation}: {exc}", code=error_code
            ) from exc
        except Exception:
            duration = perf_counter() - start
            observe_stripe_gateway_operation(
                operation=operation,
                plan_code=plan_code,
                result="exception",
                duration_seconds=duration,
            )
            logger.exception(
                "Unexpected Stripe gateway failure",
                extra={**base_context, "duration_ms": int(duration * 1000)},
            )
            raise
        else:
            duration = perf_counter() - start
            observe_stripe_gateway_operation(
                operation=operation,
                plan_code=plan_code,
                result="success",
                duration_seconds=duration,
            )
            logger.info(
                "Stripe gateway operation completed",
                extra={**base_context, "duration_ms": int(duration * 1000)},
            )
            return result


def _usage_timestamp(*, period_end: datetime | None, period_start: datetime | None) -> int:
    target = period_end or period_start or datetime.now(UTC)
    if target.tzinfo is None:
        target = target.replace(tzinfo=UTC)
    else:
        target = target.astimezone(UTC)
    return int(target.timestamp())


stripe_gateway = StripeGateway()
