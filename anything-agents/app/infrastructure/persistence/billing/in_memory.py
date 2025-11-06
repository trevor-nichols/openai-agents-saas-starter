"""Lightweight in-memory repository for billing scaffolding."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from app.domain.billing import BillingPlan, BillingRepository, TenantSubscription


class InMemoryBillingRepository(BillingRepository):
    """Minimal in-memory catalog suitable for early development."""

    def __init__(self) -> None:
        self._plans: List[BillingPlan] = [
            BillingPlan(
                code="starter",
                name="Starter",
                interval="monthly",
                interval_count=1,
                price_cents=0,
                currency="USD",
                trial_days=14,
                seat_included=1,
                feature_toggles={"enable_web_search": False},
                features=[],
            ),
            BillingPlan(
                code="pro",
                name="Pro",
                interval="monthly",
                interval_count=1,
                price_cents=9900,
                currency="USD",
                trial_days=14,
                seat_included=5,
                feature_toggles={"enable_web_search": True},
                features=[],
            ),
        ]
        self._subscriptions: dict[str, TenantSubscription] = {}
        self._usage_records: list[dict[str, object]] = []

    async def list_plans(self) -> list[BillingPlan]:
        return list(self._plans)

    async def get_subscription(self, tenant_id: str) -> TenantSubscription | None:
        return self._subscriptions.get(tenant_id)

    async def upsert_subscription(self, subscription: TenantSubscription) -> None:
        self._subscriptions[subscription.tenant_id] = subscription

    async def update_subscription(
        self,
        tenant_id: str,
        *,
        auto_renew: bool | None = None,
        billing_email: str | None = None,
        seat_count: int | None = None,
    ) -> TenantSubscription:
        subscription = self._subscriptions.get(tenant_id)
        if subscription is None:
            raise ValueError(f"Tenant '{tenant_id}' does not have a subscription.")

        if auto_renew is not None:
            subscription.auto_renew = auto_renew
        if billing_email is not None:
            subscription.billing_email = billing_email
        if seat_count is not None:
            subscription.seat_count = seat_count

        self._subscriptions[tenant_id] = subscription
        return subscription

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
        self._usage_records.append(
            {
                "tenant_id": tenant_id,
                "feature_key": feature_key,
                "quantity": quantity,
                "period_start": period_start,
                "period_end": period_end,
                "idempotency_key": idempotency_key,
            }
        )

    async def seed_trial_subscription(self, tenant_id: str) -> TenantSubscription:
        plan = self._plans[0]
        subscription = TenantSubscription(
            tenant_id=tenant_id,
            plan_code=plan.code,
            status="trialing",
            auto_renew=False,
            billing_email=None,
            starts_at=datetime.now(timezone.utc),
            trial_ends_at=datetime.now(timezone.utc),
        )
        await self.upsert_subscription(subscription)
        return subscription
