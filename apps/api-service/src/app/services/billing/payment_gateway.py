"""Payment gateway abstraction for integrating with Stripe or other providers."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter
from typing import Protocol, TypeVar
from uuid import uuid4

from app.core.settings import Settings, get_settings
from app.infrastructure.stripe import (
    StripeClient,
    StripeClientError,
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
from app.observability.metrics import observe_stripe_gateway_operation

logger = logging.getLogger("api-service.services.payment_gateway")

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


@dataclass(slots=True)
class CustomerProvisionResult:
    processor: str
    customer_id: str
    billing_email: str | None = None


@dataclass(slots=True)
class PortalSessionResult:
    url: str


@dataclass(slots=True)
class PaymentMethodSummary:
    id: str
    brand: str | None
    last4: str | None
    exp_month: int | None
    exp_year: int | None
    is_default: bool = False


@dataclass(slots=True)
class SetupIntentResult:
    id: str
    client_secret: str | None


@dataclass(slots=True)
class UpcomingInvoiceLine:
    description: str | None
    amount_cents: int
    currency: str | None
    quantity: int | None
    unit_amount_cents: int | None
    price_id: str | None


@dataclass(slots=True)
class UpcomingInvoicePreviewResult:
    invoice_id: str | None
    amount_due_cents: int
    currency: str
    period_start: datetime | None
    period_end: datetime | None
    lines: list[UpcomingInvoiceLine]


@dataclass(slots=True)
class SubscriptionPlanSwapResult:
    price_id: str
    subscription_item_id: str | None
    current_period_start: datetime | None
    current_period_end: datetime | None
    quantity: int | None
    metadata: dict[str, str] | None = None


@dataclass(slots=True)
class SubscriptionPlanScheduleResult:
    schedule_id: str
    price_id: str
    current_period_start: datetime | None
    current_period_end: datetime | None
    quantity: int | None
    metadata: dict[str, str] | None = None


class PaymentGateway(Protocol):
    """Interface for subscription lifecycle interactions with a payment provider."""

    async def create_customer(
        self,
        *,
        tenant_id: str,
        billing_email: str | None,
    ) -> CustomerProvisionResult: ...

    async def start_subscription(
        self,
        *,
        tenant_id: str,
        plan_code: str,
        billing_email: str | None,
        auto_renew: bool,
        seat_count: int | None,
        trial_days: int | None,
        customer_id: str | None = None,
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

    async def create_portal_session(
        self, *, customer_id: str, return_url: str
    ) -> PortalSessionResult: ...

    async def list_payment_methods(
        self, *, customer_id: str
    ) -> list[PaymentMethodSummary]: ...

    async def create_setup_intent(
        self, *, customer_id: str
    ) -> SetupIntentResult: ...

    async def set_default_payment_method(
        self, *, customer_id: str, payment_method_id: str
    ) -> None: ...

    async def detach_payment_method(
        self, *, customer_id: str, payment_method_id: str
    ) -> None: ...

    async def preview_upcoming_invoice(
        self,
        *,
        subscription_id: str,
        seat_count: int | None,
        proration_behavior: str | None = None,
    ) -> UpcomingInvoicePreviewResult: ...

    async def swap_subscription_plan(
        self,
        subscription_id: str,
        *,
        plan_code: str,
        seat_count: int | None,
        schedule_id: str | None = None,
        proration_behavior: str | None = None,
    ) -> SubscriptionPlanSwapResult: ...

    async def schedule_subscription_plan(
        self,
        subscription_id: str,
        *,
        plan_code: str,
        seat_count: int | None,
    ) -> SubscriptionPlanScheduleResult: ...


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

    async def create_customer(
        self, *, tenant_id: str, billing_email: str | None
    ) -> CustomerProvisionResult:
        async def _action() -> CustomerProvisionResult:
            client = self._get_client()
            customer = await client.create_customer(email=billing_email, tenant_id=tenant_id)
            return CustomerProvisionResult(
                processor=self.processor_name,
                customer_id=customer.id,
                billing_email=customer.email,
            )

        return await self._execute_operation(
            operation="create_customer",
            plan_code=None,
            tenant_id=tenant_id,
            subscription_id=None,
            context={"has_billing_email": bool(billing_email)},
            action=_action,
        )

    async def start_subscription(
        self,
        *,
        tenant_id: str,
        plan_code: str,
        billing_email: str | None,
        auto_renew: bool,
        seat_count: int | None,
        trial_days: int | None,
        customer_id: str | None = None,
    ) -> SubscriptionProvisionResult:
        quantity = seat_count or 1
        effective_trial = trial_days if trial_days and trial_days > 0 else None

        async def _action() -> SubscriptionProvisionResult:
            client = self._get_client()
            price_id = self._resolve_price_id(plan_code)

            resolved_customer_id = customer_id
            if resolved_customer_id:
                if billing_email:
                    await client.update_customer_email(resolved_customer_id, billing_email)
            else:
                customer = await client.create_customer(
                    email=billing_email,
                    tenant_id=tenant_id,
                )
                resolved_customer_id = customer.id

            subscription = await client.create_subscription(
                customer_id=resolved_customer_id,
                price_id=price_id,
                quantity=quantity,
                auto_renew=auto_renew,
                trial_period_days=effective_trial,
                metadata={
                    "tenant_id": tenant_id,
                    "plan_code": plan_code,
                    "billing_email": billing_email or "",
                },
            )

            return SubscriptionProvisionResult(
                processor=self.processor_name,
                customer_id=resolved_customer_id,
                subscription_id=subscription.id,
                starts_at=subscription.current_period_start or datetime.now(UTC),
                current_period_start=subscription.current_period_start,
                current_period_end=subscription.current_period_end,
                trial_ends_at=subscription.trial_end,
                metadata={
                    "processor_price_id": price_id,
                    "processor_subscription_item_id": (
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
                "reuse_customer": bool(customer_id),
                "trial_days": effective_trial or 0,
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

    async def create_portal_session(
        self, *, customer_id: str, return_url: str
    ) -> PortalSessionResult:
        async def _action() -> PortalSessionResult:
            client = self._get_client()
            session = await client.create_billing_portal_session(
                customer_id=customer_id,
                return_url=return_url,
            )
            return PortalSessionResult(url=session.url)

        return await self._execute_operation(
            operation="create_portal_session",
            plan_code=None,
            tenant_id=None,
            subscription_id=None,
            context={"has_return_url": bool(return_url)},
            action=_action,
        )

    async def list_payment_methods(
        self, *, customer_id: str
    ) -> list[PaymentMethodSummary]:
        async def _action() -> list[PaymentMethodSummary]:
            client = self._get_client()
            methods = await client.list_payment_methods(customer_id)
            default_id = methods.default_payment_method_id
            return [
                PaymentMethodSummary(
                    id=item.id,
                    brand=item.brand,
                    last4=item.last4,
                    exp_month=item.exp_month,
                    exp_year=item.exp_year,
                    is_default=item.id == default_id,
                )
                for item in methods.items
            ]

        return await self._execute_operation(
            operation="list_payment_methods",
            plan_code=None,
            tenant_id=None,
            subscription_id=None,
            context=None,
            action=_action,
        )

    async def create_setup_intent(
        self, *, customer_id: str
    ) -> SetupIntentResult:
        async def _action() -> SetupIntentResult:
            client = self._get_client()
            intent = await client.create_setup_intent(customer_id)
            return SetupIntentResult(id=intent.id, client_secret=intent.client_secret)

        return await self._execute_operation(
            operation="create_setup_intent",
            plan_code=None,
            tenant_id=None,
            subscription_id=None,
            context=None,
            action=_action,
        )

    async def set_default_payment_method(
        self, *, customer_id: str, payment_method_id: str
    ) -> None:
        async def _action() -> None:
            client = self._get_client()
            await client.set_default_payment_method(
                customer_id=customer_id,
                payment_method_id=payment_method_id,
            )

        await self._execute_operation(
            operation="set_default_payment_method",
            plan_code=None,
            tenant_id=None,
            subscription_id=None,
            context={"payment_method_id": payment_method_id},
            action=_action,
        )

    async def detach_payment_method(
        self, *, customer_id: str, payment_method_id: str
    ) -> None:
        async def _action() -> None:
            client = self._get_client()
            method = await client.retrieve_payment_method(payment_method_id)
            if not method.customer_id:
                raise PaymentGatewayError(
                    "Payment method is not attached to a customer.",
                    code="payment_method_unattached",
                )
            if method.customer_id != customer_id:
                raise PaymentGatewayError(
                    "Payment method does not belong to the tenant customer.",
                    code="payment_method_mismatch",
                )
            await client.detach_payment_method(payment_method_id)

        await self._execute_operation(
            operation="detach_payment_method",
            plan_code=None,
            tenant_id=None,
            subscription_id=None,
            context={"payment_method_id": payment_method_id},
            action=_action,
        )

    async def preview_upcoming_invoice(
        self,
        *,
        subscription_id: str,
        seat_count: int | None,
        proration_behavior: str | None = None,
    ) -> UpcomingInvoicePreviewResult:
        async def _action() -> UpcomingInvoicePreviewResult:
            client = self._get_client()
            subscription = await client.retrieve_subscription(subscription_id)
            item = subscription.primary_item
            if seat_count is not None and item is None:
                raise PaymentGatewayError(
                    "Stripe subscription has no items to preview.",
                    code="missing_subscription_item",
                )
            invoice = await client.preview_upcoming_invoice(
                customer_id=subscription.customer_id,
                subscription_id=subscription_id,
                subscription_item_id=item.id if item else None,
                seat_count=seat_count,
                proration_behavior=proration_behavior,
            )
            lines = [
                UpcomingInvoiceLine(
                    description=line.description,
                    amount_cents=line.amount,
                    currency=line.currency,
                    quantity=line.quantity,
                    unit_amount_cents=line.unit_amount,
                    price_id=line.price_id,
                )
                for line in invoice.lines
            ]
            return UpcomingInvoicePreviewResult(
                invoice_id=invoice.id,
                amount_due_cents=invoice.amount_due,
                currency=invoice.currency,
                period_start=invoice.period_start,
                period_end=invoice.period_end,
                lines=lines,
            )

        return await self._execute_operation(
            operation="preview_upcoming_invoice",
            plan_code=None,
            tenant_id=None,
            subscription_id=subscription_id,
            context={"has_seat_override": seat_count is not None},
            action=_action,
        )

    async def swap_subscription_plan(
        self,
        subscription_id: str,
        *,
        plan_code: str,
        seat_count: int | None,
        schedule_id: str | None = None,
        proration_behavior: str | None = None,
    ) -> SubscriptionPlanSwapResult:
        async def _action() -> SubscriptionPlanSwapResult:
            client = self._get_client()
            price_id = self._resolve_price_id(plan_code)
            subscription = await client.retrieve_subscription(subscription_id)
            item = subscription.primary_item
            if item is None:
                raise PaymentGatewayError(
                    "Stripe subscription has no items to swap.",
                    code="missing_subscription_item",
                )

            quantity = seat_count if seat_count is not None else item.quantity or 1
            metadata = dict(subscription.metadata or {})
            metadata["plan_code"] = plan_code
            if schedule_id:
                await client.release_subscription_schedule(schedule_id)

            updated = await client.modify_subscription(
                subscription,
                price_id=price_id,
                seat_count=quantity,
                proration_behavior=proration_behavior or "always_invoice",
                metadata=metadata,
            )
            updated_item = updated.primary_item
            return SubscriptionPlanSwapResult(
                price_id=price_id,
                subscription_item_id=updated_item.id if updated_item else None,
                current_period_start=updated.current_period_start,
                current_period_end=updated.current_period_end,
                quantity=updated_item.quantity if updated_item else quantity,
                metadata=metadata,
            )

        return await self._execute_operation(
            operation="swap_subscription_plan",
            plan_code=plan_code,
            tenant_id=None,
            subscription_id=subscription_id,
            context={
                "seat_count": seat_count,
                "schedule_released": bool(schedule_id),
                "proration_behavior": proration_behavior or "always_invoice",
            },
            action=_action,
        )

    async def schedule_subscription_plan(
        self,
        subscription_id: str,
        *,
        plan_code: str,
        seat_count: int | None,
    ) -> SubscriptionPlanScheduleResult:
        async def _action() -> SubscriptionPlanScheduleResult:
            client = self._get_client()
            subscription = await client.retrieve_subscription(subscription_id)
            item = subscription.primary_item
            if item is None:
                raise PaymentGatewayError(
                    "Stripe subscription has no items to schedule.",
                    code="missing_subscription_item",
                )
            if not item.price_id:
                raise PaymentGatewayError(
                    "Stripe subscription item is missing a price identifier.",
                    code="missing_price_id",
                )
            if subscription.current_period_start is None:
                raise PaymentGatewayError(
                    "Stripe subscription is missing a billing period start.",
                    code="missing_period_start",
                )
            if subscription.current_period_end is None:
                raise PaymentGatewayError(
                    "Stripe subscription is missing a billing period end.",
                    code="missing_period_end",
                )

            price_id = self._resolve_price_id(plan_code)
            quantity = seat_count if seat_count is not None else item.quantity or 1

            schedule_id = subscription.schedule_id
            if schedule_id:
                await client.retrieve_subscription_schedule(schedule_id)
            else:
                schedule = await client.create_subscription_schedule_from_subscription(
                    subscription.id
                )
                schedule_id = schedule.id

            phases: list[SubscriptionSchedulePhasePayload] = [
                {
                    "items": [
                        {
                            "price": item.price_id,
                            "quantity": item.quantity or 1,
                        }
                    ],
                    "start_date": _to_timestamp(subscription.current_period_start),
                    "end_date": _to_timestamp(subscription.current_period_end),
                },
                {
                    "items": [{"price": price_id, "quantity": quantity}],
                    "start_date": _to_timestamp(subscription.current_period_end),
                    "proration_behavior": "none",
                    "metadata": {"plan_code": plan_code},
                },
            ]

            updated = await client.update_subscription_schedule(
                schedule_id,
                phases=phases,
                end_behavior="release",
                proration_behavior="none",
                metadata={"plan_code": plan_code},
            )

            return SubscriptionPlanScheduleResult(
                schedule_id=updated.id,
                price_id=price_id,
                current_period_start=subscription.current_period_start,
                current_period_end=subscription.current_period_end,
                quantity=quantity,
                metadata=updated.metadata if hasattr(updated, "metadata") else None,
            )

        return await self._execute_operation(
            operation="schedule_subscription_plan",
            plan_code=plan_code,
            tenant_id=None,
            subscription_id=subscription_id,
            context={
                "seat_count": seat_count,
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


def _to_timestamp(value: datetime | None) -> int:
    target = value or datetime.now(UTC)
    if target.tzinfo is None:
        target = target.replace(tzinfo=UTC)
    else:
        target = target.astimezone(UTC)
    return int(target.timestamp())


stripe_gateway = StripeGateway()
