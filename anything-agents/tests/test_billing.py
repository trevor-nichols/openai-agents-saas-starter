"""Tests covering the billing service scaffolding."""

import pytest

from app.infrastructure.persistence.billing.in_memory import InMemoryBillingRepository
from app.services.billing_service import BillingService, billing_service
from app.services.payment_gateway import StripeGateway


@pytest.mark.asyncio
async def test_billing_service_lists_default_plans():
    plans = await billing_service.list_plans()
    assert len(plans) >= 2
    assert {plan.code for plan in plans} >= {"starter", "pro"}


@pytest.mark.asyncio
async def test_start_subscription_uses_gateway_and_repository():
    service = BillingService(InMemoryBillingRepository(), StripeGateway())

    subscription = await service.start_subscription(
        tenant_id="test-tenant",
        plan_code="starter",
        billing_email="owner@example.com",
        auto_renew=True,
    )

    assert subscription.processor_subscription_id is not None

    stored = await service.get_subscription("test-tenant")
    assert stored is not None
    assert stored.plan_code == "starter"


@pytest.mark.asyncio
async def test_update_subscription_applies_changes():
    repository = InMemoryBillingRepository()
    service = BillingService(repository, StripeGateway())

    await service.start_subscription(
        tenant_id="tenant-update",
        plan_code="starter",
        billing_email="owner@example.com",
        auto_renew=True,
    )

    updated = await service.update_subscription(
        "tenant-update",
        auto_renew=False,
        seat_count=3,
        billing_email="billing@example.com",
    )

    assert updated.auto_renew is False
    assert updated.seat_count == 3
    assert updated.billing_email == "billing@example.com"


@pytest.mark.asyncio
async def test_record_usage_logs_entry():
    repository = InMemoryBillingRepository()
    service = BillingService(repository, StripeGateway())

    await service.start_subscription(
        tenant_id="tenant-usage",
        plan_code="starter",
        billing_email="owner@example.com",
        auto_renew=True,
    )

    await service.record_usage(
        "tenant-usage",
        feature_key="messages",
        quantity=5,
        idempotency_key="usage-1",
    )

    assert repository._usage_records  # type: ignore[attr-defined]
    entry = repository._usage_records[0]  # type: ignore[attr-defined]
    assert entry["quantity"] == 5
