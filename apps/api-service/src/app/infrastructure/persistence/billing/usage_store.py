"""Usage tracking persistence helpers."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.billing import UsageTotal
from app.infrastructure.persistence.billing.ids import parse_tenant_id
from app.infrastructure.persistence.billing.models import (
    SubscriptionUsage as ORMSubscriptionUsage,
)
from app.infrastructure.persistence.billing.models import (
    TenantSubscription as ORMTenantSubscription,
)
from app.infrastructure.persistence.billing.subscription_store import (
    get_subscription_row_in_session,
)


class UsageStore:
    """Persistence adapter for subscription usage records."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

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
        await self._record_usage(
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
        await self._record_usage(
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
        async with self._session_factory() as session:
            tenant_uuid = parse_tenant_id(tenant_id)
            query = (
                select(
                    ORMSubscriptionUsage.feature_key,
                    func.sum(ORMSubscriptionUsage.quantity).label("total_quantity"),
                    func.min(ORMSubscriptionUsage.period_start).label("min_period_start"),
                    func.max(ORMSubscriptionUsage.period_end).label("max_period_end"),
                    func.min(ORMSubscriptionUsage.unit).label("unit"),
                )
                .join(
                    ORMTenantSubscription,
                    ORMSubscriptionUsage.subscription_id == ORMTenantSubscription.id,
                )
                .where(ORMTenantSubscription.tenant_id == tenant_uuid)
            )

            if feature_keys:
                query = query.where(ORMSubscriptionUsage.feature_key.in_(feature_keys))
            if period_start:
                query = query.where(ORMSubscriptionUsage.period_end >= period_start)
            if period_end:
                query = query.where(ORMSubscriptionUsage.period_start <= period_end)

            query = query.group_by(ORMSubscriptionUsage.feature_key)
            result = await session.execute(query)
            rows = result.all()

        usage_totals: list[UsageTotal] = []
        for row in rows:
            if row.total_quantity is None:
                continue
            window_start = period_start or row.min_period_start
            window_end = period_end or row.max_period_end
            usage_totals.append(
                UsageTotal(
                    feature_key=row.feature_key,
                    unit=row.unit or "units",
                    quantity=int(row.total_quantity),
                    window_start=window_start,
                    window_end=window_end,
                )
            )
        return usage_totals

    async def _record_usage(
        self,
        tenant_id: str,
        *,
        feature_key: str,
        quantity: int,
        period_start: datetime,
        period_end: datetime,
        idempotency_key: str | None,
    ) -> None:
        async with self._session_factory() as session:
            subscription = await get_subscription_row_in_session(session, tenant_id)
            if subscription is None:
                raise ValueError(f"Tenant '{tenant_id}' does not have a subscription.")

            await _insert_usage_record(
                session,
                subscription_id=subscription.id,
                feature_key=feature_key,
                quantity=quantity,
                period_start=period_start,
                period_end=period_end,
                idempotency_key=idempotency_key,
            )
            await session.commit()


async def _insert_usage_record(
    session: AsyncSession,
    *,
    subscription_id: uuid.UUID,
    feature_key: str,
    quantity: int,
    period_start: datetime,
    period_end: datetime,
    idempotency_key: str | None,
) -> None:
    if idempotency_key:
        existing = await session.scalar(
            select(ORMSubscriptionUsage).where(
                ORMSubscriptionUsage.subscription_id == subscription_id,
                ORMSubscriptionUsage.feature_key == feature_key,
                ORMSubscriptionUsage.external_event_id == idempotency_key,
            )
        )
        if existing is not None:
            return

    usage = ORMSubscriptionUsage(
        id=uuid.uuid4(),
        subscription_id=subscription_id,
        feature_key=feature_key,
        unit="units",
        period_start=period_start,
        period_end=period_end,
        quantity=quantity,
        reported_at=datetime.now(UTC),
        external_event_id=idempotency_key,
    )
    session.add(usage)


__all__ = ["UsageStore"]
