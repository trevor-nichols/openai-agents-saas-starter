"""Billing customer persistence helpers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.billing import BillingCustomerRecord
from app.infrastructure.persistence.billing.ids import parse_tenant_id
from app.infrastructure.persistence.billing.mappers import to_domain_customer
from app.infrastructure.persistence.billing.models import BillingCustomer as ORMBillingCustomer


class CustomerStore:
    """Persistence adapter for billing customer records."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_customer(self, tenant_id: str, *, processor: str) -> BillingCustomerRecord | None:
        async with self._session_factory() as session:
            tenant_uuid = parse_tenant_id(tenant_id)
            result = await session.execute(
                select(ORMBillingCustomer).where(
                    ORMBillingCustomer.tenant_id == tenant_uuid,
                    ORMBillingCustomer.processor == processor,
                )
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            return to_domain_customer(row)

    async def upsert_customer(self, customer: BillingCustomerRecord) -> BillingCustomerRecord:
        async with self._session_factory() as session:
            tenant_uuid = parse_tenant_id(customer.tenant_id)
            existing = await session.scalar(
                select(ORMBillingCustomer).where(
                    ORMBillingCustomer.tenant_id == tenant_uuid,
                    ORMBillingCustomer.processor == customer.processor,
                )
            )
            if existing is None:
                entity = ORMBillingCustomer(
                    id=uuid.uuid4(),
                    tenant_id=tenant_uuid,
                    processor=customer.processor,
                    processor_customer_id=customer.processor_customer_id,
                    billing_email=customer.billing_email,
                )
                session.add(entity)
                await session.commit()
                await session.refresh(entity)
                return to_domain_customer(entity)

            existing.processor_customer_id = customer.processor_customer_id
            existing.billing_email = customer.billing_email
            existing.updated_at = datetime.now(UTC)
            await session.commit()
            await session.refresh(existing)
            return to_domain_customer(existing)


__all__ = ["CustomerStore"]
