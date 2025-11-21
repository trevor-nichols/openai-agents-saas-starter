from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import cast

import pytest
from fakeredis.aioredis import FakeRedis

from app.domain.billing import BillingPlan, PlanFeature, TenantSubscription, UsageTotal
from app.services.billing.billing_service import BillingService
from app.services.usage_policy_service import (
    InMemoryUsageTotalsCache,
    RedisUsageTotalsCache,
    UsagePolicyConfigurationError,
    UsagePolicyDecision,
    UsagePolicyService,
)


class StubBillingService:
    def __init__(
        self,
        subscription: TenantSubscription | None,
        plan: BillingPlan | None,
        totals: list[UsageTotal],
    ):
        self._subscription = subscription
        self._plan = plan
        self._totals = totals
        self.invocations = 0

    async def get_subscription(self, tenant_id: str):
        return self._subscription

    async def get_plan(self, plan_code: str):
        return self._plan

    async def get_usage_totals(self, tenant_id: str, *, feature_keys, period_start, period_end):
        self.invocations += 1
        return self._totals


@pytest.fixture
def subscription() -> TenantSubscription:
    now = datetime(2025, 1, 1, tzinfo=UTC)
    return TenantSubscription(
        tenant_id="tenant-1",
        plan_code="pro",
        status="active",
        auto_renew=True,
        billing_email="owner@example.com",
        starts_at=now,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
    )


@pytest.fixture
def plan() -> BillingPlan:
    return BillingPlan(
        code="pro",
        name="Pro",
        interval="monthly",
        interval_count=1,
        price_cents=10000,
        currency="USD",
        trial_days=14,
        feature_toggles={},
        features=[
            PlanFeature(
                key="messages",
                display_name="Messages",
                hard_limit=100,
                soft_limit=80,
                is_metered=True,
            ),
            PlanFeature(
                key="input_tokens",
                display_name="Input Tokens",
                hard_limit=None,
                soft_limit=1000,
                is_metered=True,
            ),
        ],
    )


def _usage_total(feature_key: str, quantity: int) -> UsageTotal:
    now = datetime(2025, 1, 10, tzinfo=UTC)
    return UsageTotal(
        feature_key=feature_key,
        unit="units",
        quantity=quantity,
        window_start=now,
        window_end=now + timedelta(days=1),
    )


@pytest.mark.asyncio
async def test_redis_usage_totals_cache_round_trip():
    redis = FakeRedis(decode_responses=False)
    cache = RedisUsageTotalsCache(redis=redis, ttl_seconds=60)
    totals = [_usage_total("messages", 10)]

    await cache.set("tenant:key", totals)
    cached = await cache.get("tenant:key")

    assert cached is not None
    assert cached[0].feature_key == "messages"
    assert cached[0].quantity == 10


@pytest.mark.asyncio
async def test_usage_policy_blocks_on_hard_limit(subscription, plan):
    totals = [_usage_total("messages", 150)]
    service = UsagePolicyService(
        billing_service=cast(BillingService, StubBillingService(subscription, plan, totals))
    )

    result = await service.evaluate(subscription.tenant_id)

    assert result.decision is UsagePolicyDecision.HARD_LIMIT
    assert result.violations[0].feature_key == "messages"
    assert result.violations[0].usage == 150
    assert result.plan_code == plan.code


@pytest.mark.asyncio
async def test_usage_policy_warns_on_soft_limit(subscription, plan):
    totals = [_usage_total("input_tokens", 1200)]
    service = UsagePolicyService(
        billing_service=cast(BillingService, StubBillingService(subscription, plan, totals))
    )

    result = await service.evaluate(subscription.tenant_id)

    assert result.decision is UsagePolicyDecision.SOFT_LIMIT
    assert result.warnings[0].feature_key == "input_tokens"
    assert result.plan_code == plan.code


@pytest.mark.asyncio
async def test_soft_limit_can_block(subscription, plan):
    totals = [_usage_total("input_tokens", 1500)]
    stub = StubBillingService(subscription, plan, totals)
    service = UsagePolicyService(
        billing_service=cast(BillingService, stub),
        soft_limit_mode="block",
    )

    result = await service.evaluate(subscription.tenant_id)

    assert result.decision is UsagePolicyDecision.HARD_LIMIT
    assert result.violations[0].feature_key == "input_tokens"
    assert result.plan_code == plan.code


@pytest.mark.asyncio
async def test_policy_allows_when_no_metered_features(subscription):
    empty_plan = BillingPlan(
        code="starter",
        name="Starter",
        interval="monthly",
        interval_count=1,
        price_cents=0,
        currency="USD",
        features=[],
    )
    totals: list[UsageTotal] = []
    service = UsagePolicyService(
        billing_service=cast(BillingService, StubBillingService(subscription, empty_plan, totals))
    )

    result = await service.evaluate(subscription.tenant_id)

    assert result.decision is UsagePolicyDecision.ALLOW
    assert result.plan_code == empty_plan.code


@pytest.mark.asyncio
async def test_missing_subscription_raises_configuration_error(plan):
    stub = StubBillingService(subscription=None, plan=plan, totals=[])
    service = UsagePolicyService(billing_service=cast(BillingService, stub))

    with pytest.raises(UsagePolicyConfigurationError):
        await service.evaluate("missing-tenant")


@pytest.mark.asyncio
async def test_cache_reuses_rollups(subscription, plan):
    totals = [_usage_total("messages", 10)]
    stub = StubBillingService(subscription, plan, totals)
    cache = InMemoryUsageTotalsCache(ttl_seconds=60)
    service = UsagePolicyService(
        billing_service=cast(BillingService, stub),
        cache=cache,
    )

    first = await service.evaluate(subscription.tenant_id)
    totals[0] = _usage_total("messages", 99)
    second = await service.evaluate(subscription.tenant_id)

    assert stub.invocations == 1
    assert first.decision is UsagePolicyDecision.ALLOW
    assert second.decision is UsagePolicyDecision.ALLOW
