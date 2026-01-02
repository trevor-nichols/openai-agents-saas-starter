"""Postgres-backed billing repository implementation."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.billing import (
    BillingCustomerRecord,
    BillingPlan,
    BillingRepository,
    SubscriptionInvoiceRecord,
    TenantSubscription,
    UsageTotal,
)
from app.infrastructure.persistence.billing.customer_store import CustomerStore
from app.infrastructure.persistence.billing.invoice_store import InvoiceStore
from app.infrastructure.persistence.billing.plan_store import PlanStore
from app.infrastructure.persistence.billing.subscription_store import SubscriptionStore
from app.infrastructure.persistence.billing.usage_store import UsageStore


class PostgresBillingRepository(BillingRepository):
    """Facade that delegates billing persistence to focused stores."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._plans = PlanStore(session_factory)
        self._subscriptions = SubscriptionStore(session_factory)
        self._customers = CustomerStore(session_factory)
        self._usage = UsageStore(session_factory)
        self._invoices = InvoiceStore(session_factory)

    async def list_plans(self) -> list[BillingPlan]:
        return await self._plans.list_plans()

    async def get_subscription(self, tenant_id: str) -> TenantSubscription | None:
        return await self._subscriptions.get_subscription(tenant_id)

    async def upsert_subscription(self, subscription: TenantSubscription) -> None:
        await self._subscriptions.upsert_subscription(subscription)

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

    async def get_customer(
        self, tenant_id: str, *, processor: str
    ) -> BillingCustomerRecord | None:
        return await self._customers.get_customer(tenant_id, processor=processor)

    async def upsert_customer(self, customer: BillingCustomerRecord) -> BillingCustomerRecord:
        return await self._customers.upsert_customer(customer)

    async def record_usage(
        self,
        tenant_id: str,
        *,
        feature_key: str,
        quantity: int,
        period_start: datetime,
        period_end: datetime,
        idempotency_key: str | None = None,
    ) -> None:
        await self._usage.record_usage(
            tenant_id,
            feature_key=feature_key,
            quantity=quantity,
            period_start=period_start,
            period_end=period_end,
            idempotency_key=idempotency_key,
        )

    async def record_usage_from_processor(
        self,
        tenant_id: str,
        *,
        feature_key: str,
        quantity: int,
        period_start: datetime,
        period_end: datetime,
        idempotency_key: str | None = None,
    ) -> None:
        await self._usage.record_usage_from_processor(
            tenant_id,
            feature_key=feature_key,
            quantity=quantity,
            period_start=period_start,
            period_end=period_end,
            idempotency_key=idempotency_key,
        )

    async def get_usage_totals(
        self,
        tenant_id: str,
        *,
        feature_keys: Sequence[str] | None = None,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> list[UsageTotal]:
        return await self._usage.get_usage_totals(
            tenant_id,
            feature_keys=feature_keys,
            period_start=period_start,
            period_end=period_end,
        )

    async def upsert_invoice(self, invoice: SubscriptionInvoiceRecord) -> None:
        await self._invoices.upsert_invoice(invoice)

    async def get_invoice(
        self,
        tenant_id: str,
        *,
        invoice_id: str,
    ) -> SubscriptionInvoiceRecord | None:
        return await self._invoices.get_invoice(tenant_id, invoice_id=invoice_id)

    async def list_invoices(
        self,
        tenant_id: str,
        *,
        limit: int,
        offset: int,
    ) -> list[SubscriptionInvoiceRecord]:
        return await self._invoices.list_invoices(
            tenant_id,
            limit=limit,
            offset=offset,
        )
