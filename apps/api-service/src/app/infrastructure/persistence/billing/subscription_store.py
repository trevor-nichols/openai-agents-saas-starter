"""Tenant subscription persistence helpers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.domain.billing import TenantSubscription
from app.infrastructure.persistence.billing.ids import parse_tenant_id
from app.infrastructure.persistence.billing.mappers import to_domain_subscription
from app.infrastructure.persistence.billing.metadata import serialize_subscription_metadata
from app.infrastructure.persistence.billing.models import (
    BillingPlan as ORMPlan,
)
from app.infrastructure.persistence.billing.models import (
    TenantSubscription as ORMTenantSubscription,
)


class SubscriptionStore:
    """Persistence adapter for tenant subscriptions."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_subscription(self, tenant_id: str) -> TenantSubscription | None:
        async with self._session_factory() as session:
            tenant_uuid = parse_tenant_id(tenant_id)
            result = await session.execute(
                select(ORMTenantSubscription)
                .options(selectinload(ORMTenantSubscription.plan))
                .where(ORMTenantSubscription.tenant_id == tenant_uuid)
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            return to_domain_subscription(row)

    async def upsert_subscription(self, subscription: TenantSubscription) -> None:
        async with self._session_factory() as session:
            plan_row = await session.scalar(
                select(ORMPlan).where(ORMPlan.code == subscription.plan_code)
            )
            if plan_row is None:
                raise ValueError(f"Billing plan '{subscription.plan_code}' not found.")

            tenant_uuid = parse_tenant_id(subscription.tenant_id)
            existing = await session.scalar(
                select(ORMTenantSubscription).where(ORMTenantSubscription.tenant_id == tenant_uuid)
            )

            if existing is None:
                entity = ORMTenantSubscription(
                    id=uuid.uuid4(),
                    tenant_id=tenant_uuid,
                )
                _apply_subscription_fields(entity, plan_id=plan_row.id, subscription=subscription)
                session.add(entity)
            else:
                _apply_subscription_fields(
                    existing,
                    plan_id=plan_row.id,
                    subscription=subscription,
                    touch_updated_at=True,
                )

            await session.commit()

    async def update_subscription(
        self,
        tenant_id: str,
        *,
        auto_renew: bool | None = None,
        billing_email: str | None = None,
        seat_count: int | None = None,
    ) -> TenantSubscription:
        async with self._session_factory() as session:
            tenant_uuid = parse_tenant_id(tenant_id)
            subscription = await session.scalar(
                select(ORMTenantSubscription)
                .options(selectinload(ORMTenantSubscription.plan))
                .where(ORMTenantSubscription.tenant_id == tenant_uuid)
            )
            if subscription is None:
                raise ValueError(f"Tenant '{tenant_id}' does not have a subscription.")

            if auto_renew is not None:
                subscription.auto_renew = auto_renew
            if billing_email is not None:
                subscription.billing_email = billing_email
            if seat_count is not None:
                subscription.seat_count = seat_count

            subscription.updated_at = datetime.now(UTC)
            await session.commit()
            await session.refresh(subscription)
            return to_domain_subscription(subscription)


async def get_subscription_row_in_session(
    session: AsyncSession, tenant_id: str
) -> ORMTenantSubscription | None:
    tenant_uuid = parse_tenant_id(tenant_id)
    return await session.scalar(
        select(ORMTenantSubscription).where(ORMTenantSubscription.tenant_id == tenant_uuid)
    )


def _apply_subscription_fields(
    target: ORMTenantSubscription,
    *,
    plan_id: uuid.UUID,
    subscription: TenantSubscription,
    touch_updated_at: bool = False,
) -> None:
    target.plan_id = plan_id
    target.status = subscription.status
    target.auto_renew = subscription.auto_renew
    target.billing_email = subscription.billing_email
    target.processor = subscription.processor
    target.processor_customer_id = subscription.processor_customer_id
    target.processor_subscription_id = subscription.processor_subscription_id
    target.starts_at = subscription.starts_at
    target.current_period_start = subscription.current_period_start
    target.current_period_end = subscription.current_period_end
    target.trial_ends_at = subscription.trial_ends_at
    target.cancel_at = subscription.cancel_at
    target.seat_count = subscription.seat_count
    target.metadata_json = serialize_subscription_metadata(subscription)
    if touch_updated_at:
        target.updated_at = datetime.now(UTC)


__all__ = ["SubscriptionStore", "get_subscription_row_in_session"]
