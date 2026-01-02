"""Subscription seeding helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.billing.models import BillingPlan, TenantSubscription
from app.infrastructure.persistence.tenants.models import TenantAccount
from app.services.test_fixtures.errors import TestFixtureError


async def ensure_subscription(
    session: AsyncSession,
    tenant: TenantAccount,
    *,
    plan_code: str,
    billing_email: str | None,
) -> TenantSubscription:
    plan = await session.scalar(select(BillingPlan).where(BillingPlan.code == plan_code))
    if plan is None:
        raise TestFixtureError(f"Billing plan '{plan_code}' not found.")

    subscription = await session.scalar(
        select(TenantSubscription).where(TenantSubscription.tenant_id == tenant.id)
    )

    now = datetime.now(UTC)
    next_month = now + timedelta(days=30)
    metadata = {"seeded_by": "test_fixture_service"}
    if subscription is None:
        subscription = TenantSubscription(
            id=uuid4(),
            tenant_id=tenant.id,
            plan_id=plan.id,
            status="active",
            auto_renew=True,
            billing_email=billing_email,
            processor="fixture",
            processor_customer_id=f"fixture-{tenant.id}",
            processor_subscription_id=f"fixture-sub-{tenant.id}",
            starts_at=now,
            current_period_start=now,
            current_period_end=next_month,
            seat_count=plan.seat_included or 1,
            metadata_json=metadata,
        )
        session.add(subscription)
    else:
        subscription.plan_id = plan.id
        subscription.status = "active"
        subscription.auto_renew = True
        subscription.billing_email = billing_email
        subscription.processor = subscription.processor or "fixture"
        subscription.processor_customer_id = (
            subscription.processor_customer_id or f"fixture-{tenant.id}"
        )
        subscription.processor_subscription_id = (
            subscription.processor_subscription_id or f"fixture-sub-{tenant.id}"
        )
        subscription.current_period_start = subscription.current_period_start or now
        subscription.current_period_end = subscription.current_period_end or next_month
        metadata_payload = subscription.metadata_json or {}
        metadata_payload.update(metadata)
        subscription.metadata_json = metadata_payload

    return subscription


__all__ = ["ensure_subscription"]
