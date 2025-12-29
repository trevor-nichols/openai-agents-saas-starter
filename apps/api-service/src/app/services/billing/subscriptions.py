"""Subscription orchestration for billing."""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.billing import BillingPlan, TenantSubscription
from app.services.billing.context import BillingContext
from app.services.billing.customers import BillingCustomerService
from app.services.billing.errors import (
    SubscriptionStateError,
    raise_invalid_tenant,
    raise_payment_provider,
)
from app.services.billing.models import (
    PlanChangeResult,
    PlanChangeTiming,
    UpcomingInvoiceLineSnapshot,
    UpcomingInvoicePreview,
)
from app.services.billing.payment_gateway import PaymentGatewayError
from app.services.billing.policies import resolve_plan_change_timing
from app.services.billing.queries import (
    ensure_plan_exists,
    get_subscription,
    list_plans,
    require_processor_subscription_id,
    require_subscription,
)


class BillingSubscriptionService:
    """Coordinates subscription lifecycle operations."""

    def __init__(self, context: BillingContext, *, customers: BillingCustomerService) -> None:
        self._context = context
        self._customers = customers

    async def list_plans(self) -> list[BillingPlan]:
        return await list_plans(self._context.require_repository())

    async def get_plan(self, plan_code: str) -> BillingPlan:
        return await ensure_plan_exists(self._context.require_repository(), plan_code)

    async def get_subscription(self, tenant_id: str) -> TenantSubscription | None:
        return await get_subscription(self._context.require_repository(), tenant_id)

    async def start_subscription(
        self,
        *,
        tenant_id: str,
        plan_code: str,
        billing_email: str | None,
        auto_renew: bool,
        seat_count: int | None = None,
        trial_days: int | None = None,
    ) -> TenantSubscription:
        repository = self._context.require_repository()
        plan = await ensure_plan_exists(repository, plan_code)
        resolved_seat_count = seat_count if seat_count is not None else plan.seat_included
        gateway_seat_count = resolved_seat_count if resolved_seat_count is not None else 1
        customer_record = await self._customers.resolve_customer(
            tenant_id,
            billing_email,
            create_if_missing=False,
        )
        effective_billing_email = billing_email or (
            customer_record.billing_email if customer_record else None
        )
        existing_customer_id = (
            customer_record.processor_customer_id if customer_record else None
        )
        try:
            processor_payload = await self._context.require_gateway().start_subscription(
                tenant_id=tenant_id,
                plan_code=plan_code,
                billing_email=effective_billing_email,
                auto_renew=auto_renew,
                seat_count=gateway_seat_count,
                trial_days=trial_days,
                customer_id=existing_customer_id,
            )
        except PaymentGatewayError as exc:
            raise_payment_provider(exc)

        subscription = TenantSubscription(
            tenant_id=tenant_id,
            plan_code=plan_code,
            status="active",
            auto_renew=auto_renew,
            billing_email=effective_billing_email,
            starts_at=processor_payload.starts_at,
            current_period_start=processor_payload.current_period_start,
            current_period_end=processor_payload.current_period_end,
            trial_ends_at=processor_payload.trial_ends_at,
            seat_count=resolved_seat_count,
            metadata=processor_payload.metadata or {},
            processor=processor_payload.processor,
            processor_customer_id=processor_payload.customer_id,
            processor_subscription_id=processor_payload.subscription_id,
        )

        try:
            await repository.upsert_subscription(subscription)
        except ValueError as exc:
            raise_invalid_tenant(exc)

        await self._customers.upsert_customer_record(
            tenant_id=tenant_id,
            customer_id=processor_payload.customer_id,
            billing_email=effective_billing_email,
            processor=processor_payload.processor,
        )
        return subscription

    async def cancel_subscription(
        self,
        tenant_id: str,
        cancel_at_period_end: bool = True,
    ) -> TenantSubscription:
        repository = self._context.require_repository()
        subscription = await require_subscription(repository, tenant_id)
        processor_subscription_id = require_processor_subscription_id(subscription)

        try:
            await self._context.require_gateway().cancel_subscription(
                processor_subscription_id,
                cancel_at_period_end=cancel_at_period_end,
            )
        except PaymentGatewayError as exc:
            raise_payment_provider(exc)

        if cancel_at_period_end:
            subscription.cancel_at = subscription.current_period_end
        else:
            subscription.status = "canceled"
            subscription.cancel_at = datetime.now(UTC)

        try:
            await repository.upsert_subscription(subscription)
        except ValueError as exc:
            raise_invalid_tenant(exc)
        return subscription

    async def update_subscription(
        self,
        tenant_id: str,
        *,
        auto_renew: bool | None = None,
        billing_email: str | None = None,
        seat_count: int | None = None,
    ) -> TenantSubscription:
        repository = self._context.require_repository()
        subscription = await require_subscription(repository, tenant_id)

        if subscription.processor_subscription_id:
            try:
                await self._context.require_gateway().update_subscription(
                    subscription.processor_subscription_id,
                    auto_renew=auto_renew,
                    seat_count=seat_count,
                    billing_email=billing_email,
                )
            except PaymentGatewayError as exc:
                raise_payment_provider(exc)

        try:
            updated = await repository.update_subscription(
                tenant_id,
                auto_renew=auto_renew,
                billing_email=billing_email,
                seat_count=seat_count,
            )
        except ValueError as exc:
            raise_invalid_tenant(exc)

        if updated.processor_customer_id:
            await self._customers.upsert_customer_record(
                tenant_id=tenant_id,
                customer_id=updated.processor_customer_id,
                billing_email=updated.billing_email,
            )
        return updated

    async def change_subscription_plan(
        self,
        *,
        tenant_id: str,
        plan_code: str,
        seat_count: int | None = None,
        timing: PlanChangeTiming = PlanChangeTiming.AUTO,
    ) -> PlanChangeResult:
        repository = self._context.require_repository()
        subscription = await require_subscription(repository, tenant_id)
        current_plan = await ensure_plan_exists(repository, subscription.plan_code)
        target_plan = await ensure_plan_exists(repository, plan_code)

        if subscription.pending_plan_code == plan_code:
            raise SubscriptionStateError("A plan change is already scheduled for this plan.")
        if subscription.plan_code == plan_code:
            raise SubscriptionStateError("Subscription is already on the requested plan.")
        processor_subscription_id = require_processor_subscription_id(subscription)

        effective_seat_count = (
            seat_count
            if seat_count is not None
            else subscription.seat_count
            or target_plan.seat_included
            or current_plan.seat_included
            or 1
        )
        current_seat_count = (
            subscription.seat_count
            if subscription.seat_count is not None
            else current_plan.seat_included
            or 1
        )
        resolved_timing = resolve_plan_change_timing(
            timing,
            current_plan=current_plan,
            target_plan=target_plan,
            current_seat_count=current_seat_count,
            target_seat_count=effective_seat_count,
        )

        effective_at: datetime | None
        if resolved_timing == PlanChangeTiming.IMMEDIATE:
            try:
                swap_result = await self._context.require_gateway().swap_subscription_plan(
                    processor_subscription_id,
                    plan_code=plan_code,
                    seat_count=effective_seat_count,
                    schedule_id=subscription.processor_schedule_id,
                    proration_behavior="always_invoice",
                )
            except PaymentGatewayError as exc:
                raise_payment_provider(exc)

            subscription.plan_code = target_plan.code
            subscription.seat_count = effective_seat_count
            subscription.pending_plan_code = None
            subscription.pending_plan_effective_at = None
            subscription.pending_seat_count = None
            subscription.processor_schedule_id = None
            subscription.current_period_start = (
                swap_result.current_period_start or subscription.current_period_start
            )
            subscription.current_period_end = (
                swap_result.current_period_end or subscription.current_period_end
            )

            metadata = dict(subscription.metadata or {})
            metadata["processor_price_id"] = swap_result.price_id
            if swap_result.subscription_item_id:
                metadata["processor_subscription_item_id"] = swap_result.subscription_item_id
            subscription.metadata = metadata

            effective_at = datetime.now(UTC)
        else:
            try:
                schedule_result = await self._context.require_gateway().schedule_subscription_plan(
                    processor_subscription_id,
                    plan_code=plan_code,
                    seat_count=effective_seat_count,
                )
            except PaymentGatewayError as exc:
                raise_payment_provider(exc)

            subscription.pending_plan_code = plan_code
            subscription.pending_plan_effective_at = schedule_result.current_period_end
            subscription.pending_seat_count = effective_seat_count
            subscription.processor_schedule_id = schedule_result.schedule_id
            subscription.current_period_start = (
                schedule_result.current_period_start or subscription.current_period_start
            )
            subscription.current_period_end = (
                schedule_result.current_period_end or subscription.current_period_end
            )
            effective_at = subscription.pending_plan_effective_at

        try:
            await repository.upsert_subscription(subscription)
        except ValueError as exc:
            raise_invalid_tenant(exc)

        return PlanChangeResult(
            subscription=subscription,
            target_plan_code=plan_code,
            effective_at=effective_at,
            seat_count=effective_seat_count,
            timing=resolved_timing,
        )

    async def preview_upcoming_invoice(
        self,
        tenant_id: str,
        *,
        seat_count: int | None,
    ) -> UpcomingInvoicePreview:
        repository = self._context.require_repository()
        subscription = await require_subscription(repository, tenant_id)
        processor_subscription_id = require_processor_subscription_id(subscription)

        plan = await ensure_plan_exists(repository, subscription.plan_code)
        effective_seat_count = (
            seat_count
            if seat_count is not None
            else subscription.seat_count or plan.seat_included
        )

        try:
            preview = await self._context.require_gateway().preview_upcoming_invoice(
                subscription_id=processor_subscription_id,
                seat_count=effective_seat_count,
            )
        except PaymentGatewayError as exc:
            raise_payment_provider(exc)

        return UpcomingInvoicePreview(
            plan_code=subscription.plan_code,
            plan_name=plan.name,
            seat_count=effective_seat_count,
            invoice_id=preview.invoice_id,
            amount_due_cents=preview.amount_due_cents,
            currency=preview.currency,
            period_start=preview.period_start,
            period_end=preview.period_end,
            lines=[
                UpcomingInvoiceLineSnapshot(
                    description=line.description,
                    amount_cents=line.amount_cents,
                    currency=line.currency,
                    quantity=line.quantity,
                    unit_amount_cents=line.unit_amount_cents,
                    price_id=line.price_id,
                )
                for line in preview.lines
            ],
        )


__all__ = ["BillingSubscriptionService"]
