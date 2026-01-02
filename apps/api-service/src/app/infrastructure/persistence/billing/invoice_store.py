"""Subscription invoice persistence helpers."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.billing import SubscriptionInvoiceRecord
from app.infrastructure.persistence.billing.ids import parse_tenant_id
from app.infrastructure.persistence.billing.mappers import to_domain_invoice
from app.infrastructure.persistence.billing.models import (
    SubscriptionInvoice as ORMSubscriptionInvoice,
)
from app.infrastructure.persistence.billing.models import (
    TenantSubscription as ORMTenantSubscription,
)
from app.infrastructure.persistence.billing.subscription_store import (
    get_subscription_row_in_session,
)


class InvoiceStore:
    """Persistence adapter for subscription invoices."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def upsert_invoice(self, invoice: SubscriptionInvoiceRecord) -> None:
        async with self._session_factory() as session:
            subscription = await get_subscription_row_in_session(session, invoice.tenant_id)
            if subscription is None:
                raise ValueError(f"Tenant '{invoice.tenant_id}' does not have a subscription.")

            existing = None
            if invoice.processor_invoice_id:
                existing = await session.scalar(
                    select(ORMSubscriptionInvoice)
                    .where(ORMSubscriptionInvoice.subscription_id == subscription.id)
                    .where(
                        ORMSubscriptionInvoice.external_invoice_id == invoice.processor_invoice_id
                    )
                )
            if existing is None:
                existing = await session.scalar(
                    select(ORMSubscriptionInvoice)
                    .where(ORMSubscriptionInvoice.subscription_id == subscription.id)
                    .where(ORMSubscriptionInvoice.period_start == invoice.period_start)
                )

            if existing is None:
                entity = ORMSubscriptionInvoice(
                    id=uuid.uuid4(),
                    subscription_id=subscription.id,
                    period_start=invoice.period_start,
                    period_end=invoice.period_end,
                    amount_cents=invoice.amount_cents,
                    currency=invoice.currency,
                    status=invoice.status,
                    external_invoice_id=invoice.processor_invoice_id,
                    hosted_invoice_url=invoice.hosted_invoice_url,
                )
                session.add(entity)
            else:
                existing.period_start = invoice.period_start
                existing.period_end = invoice.period_end
                existing.amount_cents = invoice.amount_cents
                existing.currency = invoice.currency
                existing.status = invoice.status
                existing.external_invoice_id = invoice.processor_invoice_id
                existing.hosted_invoice_url = invoice.hosted_invoice_url

            await session.commit()

    async def get_invoice(
        self,
        tenant_id: str,
        *,
        invoice_id: str,
    ) -> SubscriptionInvoiceRecord | None:
        async with self._session_factory() as session:
            tenant_uuid = parse_tenant_id(tenant_id)
            result = await session.execute(
                select(ORMSubscriptionInvoice)
                .join(
                    ORMTenantSubscription,
                    ORMSubscriptionInvoice.subscription_id == ORMTenantSubscription.id,
                )
                .where(ORMTenantSubscription.tenant_id == tenant_uuid)
                .where(ORMSubscriptionInvoice.external_invoice_id == invoice_id)
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            return to_domain_invoice(row, tenant_id=str(tenant_uuid))

    async def list_invoices(
        self,
        tenant_id: str,
        *,
        limit: int,
        offset: int,
    ) -> list[SubscriptionInvoiceRecord]:
        async with self._session_factory() as session:
            tenant_uuid = parse_tenant_id(tenant_id)
            result = await session.execute(
                select(ORMSubscriptionInvoice)
                .join(
                    ORMTenantSubscription,
                    ORMSubscriptionInvoice.subscription_id == ORMTenantSubscription.id,
                )
                .where(ORMTenantSubscription.tenant_id == tenant_uuid)
                .order_by(
                    ORMSubscriptionInvoice.period_start.desc(),
                    ORMSubscriptionInvoice.created_at.desc(),
                )
                .limit(limit)
                .offset(offset)
            )
            rows = result.scalars().all()
            return [to_domain_invoice(row, tenant_id=str(tenant_uuid)) for row in rows]


__all__ = ["InvoiceStore"]
