"""Stripe-backed implementation of the payment gateway."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from app.core.settings import Settings, get_settings
from app.infrastructure.stripe import StripeClient
from app.infrastructure.stripe.types import SubscriptionSchedulePhasePayload
from app.services.billing.payment_gateway import (
    CustomerProvisionResult,
    PaymentGateway,
    PaymentGatewayError,
    PaymentMethodSummary,
    PortalSessionResult,
    SetupIntentResult,
    SubscriptionPlanScheduleResult,
    SubscriptionPlanSwapResult,
    SubscriptionProvisionResult,
    UpcomingInvoicePreviewResult,
)
from app.services.billing.stripe.client_protocol import StripeGatewayClient
from app.services.billing.stripe.mapping import (
    build_payment_method_summaries,
    build_upcoming_invoice_preview,
)
from app.services.billing.stripe.plan_mapping import resolve_price_id
from app.services.billing.stripe.telemetry import execute_gateway_operation
from app.services.billing.stripe.utils import (
    ensure_primary_item,
    require_period_end,
    require_period_start,
    resolve_quantity,
    to_utc_timestamp,
    usage_timestamp,
)

logger = logging.getLogger("api-service.services.payment_gateway")

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

        return await execute_gateway_operation(
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
            price_id = resolve_price_id(plan_code, settings_factory=self._settings_factory)

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

        return await execute_gateway_operation(
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

        await execute_gateway_operation(
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

        await execute_gateway_operation(
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

        return await execute_gateway_operation(
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
            return build_payment_method_summaries(methods)

        return await execute_gateway_operation(
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

        return await execute_gateway_operation(
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

        await execute_gateway_operation(
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

        await execute_gateway_operation(
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
            if seat_count is not None:
                item = ensure_primary_item(
                    subscription,
                    message="Stripe subscription has no items to preview.",
                    error_code="missing_subscription_item",
                )
            invoice = await client.preview_upcoming_invoice(
                customer_id=subscription.customer_id,
                subscription_id=subscription_id,
                subscription_item_id=item.id if item else None,
                seat_count=seat_count,
                proration_behavior=proration_behavior,
            )
            return build_upcoming_invoice_preview(invoice)

        return await execute_gateway_operation(
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
            price_id = resolve_price_id(plan_code, settings_factory=self._settings_factory)
            subscription = await client.retrieve_subscription(subscription_id)
            item = ensure_primary_item(
                subscription,
                message="Stripe subscription has no items to swap.",
                error_code="missing_subscription_item",
            )

            quantity = resolve_quantity(item, seat_count)
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

        return await execute_gateway_operation(
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
            item = ensure_primary_item(
                subscription,
                message="Stripe subscription has no items to schedule.",
                error_code="missing_subscription_item",
            )
            if not item.price_id:
                raise PaymentGatewayError(
                    "Stripe subscription item is missing a price identifier.",
                    code="missing_price_id",
                )
            period_start = require_period_start(subscription)
            period_end = require_period_end(subscription)

            price_id = resolve_price_id(plan_code, settings_factory=self._settings_factory)
            quantity = resolve_quantity(item, seat_count)

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
                    "start_date": to_utc_timestamp(period_start),
                    "end_date": to_utc_timestamp(period_end),
                },
                {
                    "items": [{"price": price_id, "quantity": quantity}],
                    "start_date": to_utc_timestamp(period_end),
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
                current_period_start=period_start,
                current_period_end=period_end,
                quantity=quantity,
                metadata=updated.metadata if hasattr(updated, "metadata") else None,
            )

        return await execute_gateway_operation(
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
            item = ensure_primary_item(
                subscription,
                message="Stripe subscription has no metered items for usage recording.",
                error_code="missing_metered_item",
            )

            timestamp = usage_timestamp(period_end=period_end, period_start=period_start)
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

        await execute_gateway_operation(
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


_stripe_gateway: StripeGateway | None = None


def get_stripe_gateway() -> StripeGateway:
    """Return a shared Stripe gateway instance."""

    global _stripe_gateway
    if _stripe_gateway is None:
        _stripe_gateway = StripeGateway()
    return _stripe_gateway


__all__ = ["StripeGateway", "get_stripe_gateway"]
