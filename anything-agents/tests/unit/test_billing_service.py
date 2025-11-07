"""Tests covering the billing service scaffolding."""

from datetime import datetime, timezone

import pytest

from app.infrastructure.persistence.billing.in_memory import InMemoryBillingRepository
from app.services.billing_service import (
    BillingService,
    PaymentProviderError,
    billing_service,
)
from app.services.payment_gateway import (
    PaymentGateway,
    PaymentGatewayError,
    SubscriptionProvisionResult,
)


class FakeGateway(PaymentGateway):
    """In-memory gateway used for service tests."""

    def __init__(self) -> None:
        self.subscription_counter = 0
        self.last_quantity: int | None = None
        self.usage_records: list[dict[str, object]] = []

    async def start_subscription(
        self,
        *,
        tenant_id: str,
        plan_code: str,
        billing_email: str | None,
        auto_renew: bool,
        seat_count: int | None,
    ) -> SubscriptionProvisionResult:
        self.subscription_counter += 1
        now = datetime.now(timezone.utc)
        self.last_quantity = seat_count or 1
        return SubscriptionProvisionResult(
            processor="stub",
            customer_id=f"cust_{tenant_id}",
            subscription_id=f"sub_{self.subscription_counter}",
            starts_at=now,
            current_period_start=now,
            current_period_end=now,
            metadata={"tenant_id": tenant_id, "plan_code": plan_code},
        )

    async def update_subscription(
        self,
        subscription_id: str,
        *,
        auto_renew: bool | None = None,
        seat_count: int | None = None,
        billing_email: str | None = None,
    ) -> None:
        if seat_count is not None:
            self.last_quantity = seat_count

    async def cancel_subscription(
        self,
        subscription_id: str,
        *,
        cancel_at_period_end: bool,
    ) -> None:
        return None

    async def record_usage(
        self,
        subscription_id: str,
        *,
        feature_key: str,
        quantity: int,
        idempotency_key: str | None,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> None:
        self.usage_records.append(
            {
                "subscription_id": subscription_id,
                "feature_key": feature_key,
                "quantity": quantity,
                "idempotency_key": idempotency_key,
            }
        )


class ErrorGateway(FakeGateway):
    async def start_subscription(self, **_: object) -> SubscriptionProvisionResult:  # type: ignore[override]
        raise PaymentGatewayError("boom")


@pytest.mark.asyncio
async def test_billing_service_lists_default_plans():
    plans = await billing_service.list_plans()
    assert len(plans) >= 2
    assert {plan.code for plan in plans} >= {"starter", "pro"}


@pytest.mark.asyncio
async def test_start_subscription_uses_gateway_and_repository():
    service = BillingService(InMemoryBillingRepository(), FakeGateway())

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
    gateway = FakeGateway()
    service = BillingService(repository, gateway)

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
    service = BillingService(repository, FakeGateway())

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


@pytest.mark.asyncio
async def test_gateway_errors_surface_as_payment_provider_error():
    service = BillingService(InMemoryBillingRepository(), ErrorGateway())

    with pytest.raises(PaymentProviderError):
        await service.start_subscription(
            tenant_id="boom",
            plan_code="starter",
            billing_email=None,
            auto_renew=True,
        )
