"""Usage seeding helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.billing.models import SubscriptionUsage, TenantSubscription
from app.infrastructure.persistence.tenants.models import TenantAccount
from app.infrastructure.persistence.usage.models import UsageCounter, UsageCounterGranularity
from app.services.test_fixtures.schemas import (
    FixtureUsageCounter,
    FixtureUsageEntry,
    FixtureUserResult,
)
from app.services.test_fixtures.seeders.resolve import resolve_user_id


async def ensure_usage_records(
    session: AsyncSession,
    subscription: TenantSubscription,
    usage_entries: list[FixtureUsageEntry],
) -> None:
    for entry in usage_entries:
        period_start = _ensure_utc(entry.period_start)
        period_end = _ensure_utc(entry.period_end or (period_start + timedelta(days=1)))

        existing = await session.scalar(
            select(SubscriptionUsage).where(
                SubscriptionUsage.subscription_id == subscription.id,
                SubscriptionUsage.feature_key == entry.feature_key,
                SubscriptionUsage.period_start == period_start,
            )
        )

        if existing:
            existing.quantity = entry.quantity
            existing.period_end = period_end
            existing.unit = entry.unit
            existing.external_event_id = entry.idempotency_key or existing.external_event_id
        else:
            session.add(
                SubscriptionUsage(
                    id=uuid4(),
                    subscription_id=subscription.id,
                    feature_key=entry.feature_key,
                    unit=entry.unit,
                    period_start=period_start,
                    period_end=period_end,
                    quantity=entry.quantity,
                    external_event_id=entry.idempotency_key,
                )
            )


async def ensure_usage_counters(
    session: AsyncSession,
    tenant: TenantAccount,
    user_results: dict[str, FixtureUserResult],
    usage_counters: list[FixtureUsageCounter],
) -> None:
    now = datetime.now(UTC)
    for entry in usage_counters:
        user_id = resolve_user_id(entry.user_email, user_results) if entry.user_email else None
        granularity = UsageCounterGranularity(entry.granularity)
        stmt = select(UsageCounter).where(
            UsageCounter.tenant_id == tenant.id,
            UsageCounter.period_start == entry.period_start,
            UsageCounter.granularity == granularity,
        )
        if user_id is None:
            stmt = stmt.where(UsageCounter.user_id.is_(None))
        else:
            stmt = stmt.where(UsageCounter.user_id == user_id)

        existing = await session.scalar(stmt)
        if existing:
            existing.input_tokens = entry.input_tokens
            existing.output_tokens = entry.output_tokens
            existing.requests = entry.requests
            existing.storage_bytes = entry.storage_bytes
            existing.updated_at = now
        else:
            session.add(
                UsageCounter(
                    id=uuid4(),
                    tenant_id=tenant.id,
                    user_id=user_id,
                    period_start=entry.period_start,
                    granularity=granularity,
                    input_tokens=entry.input_tokens,
                    output_tokens=entry.output_tokens,
                    requests=entry.requests,
                    storage_bytes=entry.storage_bytes,
                    created_at=now,
                    updated_at=now,
                )
            )


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = ["ensure_usage_counters", "ensure_usage_records"]
