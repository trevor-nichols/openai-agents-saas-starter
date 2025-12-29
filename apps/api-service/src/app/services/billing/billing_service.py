"""Service layer for billing plan and subscription management."""

from __future__ import annotations

from datetime import datetime

from app.domain.billing import BillingPlan, BillingRepository, TenantSubscription, UsageTotal
from app.services.billing.context import BillingContext
from app.services.billing.customers import BillingCustomerService
from app.services.billing.models import (
    PlanChangeResult,
    PlanChangeTiming,
    ProcessorInvoiceSnapshot,
    ProcessorSubscriptionSnapshot,
    UpcomingInvoicePreview,
)
from app.services.billing.payment_gateway import (
    PaymentGateway,
    PaymentMethodSummary,
    PortalSessionResult,
    SetupIntentResult,
)
from app.services.billing.processor_sync import BillingProcessorSyncService
from app.services.billing.stripe.gateway import get_stripe_gateway
from app.services.billing.subscriptions import BillingSubscriptionService
from app.services.billing.usage import BillingUsageService


class BillingService:
    """Facade that wires specialized billing services."""

    def __init__(
        self,
        repository: BillingRepository | None = None,
        gateway: PaymentGateway | None = None,
        *,
        processor_name: str = "stripe",
    ) -> None:
        self._context = BillingContext(
            repository=repository,
            gateway=gateway or get_stripe_gateway(),
        )
        self._customers = BillingCustomerService(
            self._context,
            processor_name=processor_name,
        )
        self._subscriptions = BillingSubscriptionService(
            self._context,
            customers=self._customers,
        )
        self._usage = BillingUsageService(self._context)
        self._processor_sync = BillingProcessorSyncService(
            self._context,
            customers=self._customers,
        )

    def set_repository(self, repository: BillingRepository) -> None:
        self._context.repository = repository

    def set_gateway(self, gateway: PaymentGateway) -> None:
        self._context.gateway = gateway

    async def list_plans(self) -> list[BillingPlan]:
        return await self._subscriptions.list_plans()

    async def get_plan(self, plan_code: str) -> BillingPlan:
        return await self._subscriptions.get_plan(plan_code)

    async def get_subscription(self, tenant_id: str) -> TenantSubscription | None:
        return await self._subscriptions.get_subscription(tenant_id)

    async def get_usage_totals(
        self,
        tenant_id: str,
        *,
        feature_keys: list[str] | None = None,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> list[UsageTotal]:
        return await self._usage.get_usage_totals(
            tenant_id,
            feature_keys=feature_keys,
            period_start=period_start,
            period_end=period_end,
        )

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
        return await self._subscriptions.start_subscription(
            tenant_id=tenant_id,
            plan_code=plan_code,
            billing_email=billing_email,
            auto_renew=auto_renew,
            seat_count=seat_count,
            trial_days=trial_days,
        )

    async def cancel_subscription(
        self,
        tenant_id: str,
        cancel_at_period_end: bool = True,
    ) -> TenantSubscription:
        return await self._subscriptions.cancel_subscription(
            tenant_id,
            cancel_at_period_end=cancel_at_period_end,
        )

    async def record_usage(
        self,
        tenant_id: str,
        feature_key: str,
        quantity: int,
        idempotency_key: str | None = None,
        *,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> None:
        await self._usage.record_usage(
            tenant_id,
            feature_key=feature_key,
            quantity=quantity,
            idempotency_key=idempotency_key,
            period_start=period_start,
            period_end=period_end,
        )

    async def update_subscription(
        self,
        tenant_id: str,
        *,
        auto_renew: bool | None = None,
        billing_email: str | None = None,
        seat_count: int | None = None,
    ) -> TenantSubscription:
        return await self._subscriptions.update_subscription(
            tenant_id,
            auto_renew=auto_renew,
            billing_email=billing_email,
            seat_count=seat_count,
        )

    async def change_subscription_plan(
        self,
        *,
        tenant_id: str,
        plan_code: str,
        seat_count: int | None = None,
        timing: PlanChangeTiming = PlanChangeTiming.AUTO,
    ) -> PlanChangeResult:
        return await self._subscriptions.change_subscription_plan(
            tenant_id=tenant_id,
            plan_code=plan_code,
            seat_count=seat_count,
            timing=timing,
        )

    async def create_portal_session(
        self,
        tenant_id: str,
        *,
        billing_email: str | None = None,
    ) -> PortalSessionResult:
        return await self._customers.create_portal_session(
            tenant_id,
            billing_email=billing_email,
        )

    async def list_payment_methods(
        self, tenant_id: str
    ) -> list[PaymentMethodSummary]:
        return await self._customers.list_payment_methods(tenant_id)

    async def create_setup_intent(
        self,
        tenant_id: str,
        *,
        billing_email: str | None = None,
    ) -> SetupIntentResult:
        return await self._customers.create_setup_intent(
            tenant_id,
            billing_email=billing_email,
        )

    async def set_default_payment_method(
        self,
        tenant_id: str,
        *,
        payment_method_id: str,
    ) -> None:
        await self._customers.set_default_payment_method(
            tenant_id,
            payment_method_id=payment_method_id,
        )

    async def detach_payment_method(
        self,
        tenant_id: str,
        *,
        payment_method_id: str,
    ) -> None:
        await self._customers.detach_payment_method(
            tenant_id,
            payment_method_id=payment_method_id,
        )

    async def preview_upcoming_invoice(
        self,
        tenant_id: str,
        *,
        seat_count: int | None,
    ) -> UpcomingInvoicePreview:
        return await self._subscriptions.preview_upcoming_invoice(
            tenant_id,
            seat_count=seat_count,
        )

    async def sync_subscription_from_processor(
        self,
        snapshot: ProcessorSubscriptionSnapshot,
        *,
        processor_name: str = "stripe",
    ) -> TenantSubscription:
        return await self._processor_sync.sync_subscription_from_processor(
            snapshot,
            processor_name=processor_name,
        )

    async def ingest_invoice_snapshot(
        self,
        snapshot: ProcessorInvoiceSnapshot,
    ) -> None:
        await self._processor_sync.ingest_invoice_snapshot(snapshot)


def get_billing_service() -> BillingService:
    """Resolve the active billing service from the application container."""

    from app.bootstrap.container import get_container

    return get_container().billing_service


class _BillingServiceHandle:
    """Proxy exposing the container-backed billing service."""

    def __getattr__(self, name: str):
        return getattr(get_billing_service(), name)


billing_service = _BillingServiceHandle()
