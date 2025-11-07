"""Tests covering the billing service scaffolding."""

from datetime import datetime, timezone
from types import SimpleNamespace
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.persistence.billing.postgres import PostgresBillingRepository
from app.infrastructure.persistence.conversations import models as persistence_models
from app.services.billing_service import (
    BillingService,
    PaymentProviderError,
)
from app.services.payment_gateway import (
    PaymentGateway,
    PaymentGatewayError,
    SubscriptionProvisionResult,
)


class FakeGateway(PaymentGateway):
    """Stub gateway used for service tests."""

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


@pytest.fixture
async def billing_context():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(persistence_models.Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    tenant_id = uuid.uuid4()

    async with session_factory() as session:
        session.add(
            persistence_models.TenantAccount(
                id=tenant_id,
                slug="tenant",
                name="Test Tenant",
            )
        )
        session.add_all(_default_plans())
        await session.commit()

    repository = PostgresBillingRepository(session_factory)

    context = SimpleNamespace(
        tenant_id=str(tenant_id),
        repository=repository,
        session_factory=session_factory,
    )
    try:
        yield context
    finally:
        await engine.dispose()


def _default_plans():
    starter = persistence_models.BillingPlan(
        code="starter",
        name="Starter",
        interval="monthly",
        interval_count=1,
        price_cents=0,
        currency="USD",
        trial_days=14,
        seat_included=1,
        feature_toggles={"enable_web_search": False},
    )
    pro = persistence_models.BillingPlan(
        code="pro",
        name="Pro",
        interval="monthly",
        interval_count=1,
        price_cents=9900,
        currency="USD",
        trial_days=14,
        seat_included=5,
        feature_toggles={"enable_web_search": True},
    )
    return [starter, pro]


def _service(context: SimpleNamespace, gateway: PaymentGateway | None = None) -> BillingService:
    return BillingService(context.repository, gateway or FakeGateway())


@pytest.mark.asyncio
async def test_billing_service_lists_default_plans(billing_context):
    service = _service(billing_context)
    plans = await service.list_plans()
    assert len(plans) >= 2
    assert {plan.code for plan in plans} >= {"starter", "pro"}


@pytest.mark.asyncio
async def test_start_subscription_uses_gateway_and_repository(billing_context):
    service = _service(billing_context)

    subscription = await service.start_subscription(
        tenant_id=billing_context.tenant_id,
        plan_code="starter",
        billing_email="owner@example.com",
        auto_renew=True,
    )

    assert subscription.processor_subscription_id is not None

    stored = await service.get_subscription(billing_context.tenant_id)
    assert stored is not None
    assert stored.plan_code == "starter"


@pytest.mark.asyncio
async def test_update_subscription_applies_changes(billing_context):
    gateway = FakeGateway()
    service = BillingService(billing_context.repository, gateway)

    await service.start_subscription(
        tenant_id=billing_context.tenant_id,
        plan_code="starter",
        billing_email="owner@example.com",
        auto_renew=True,
    )

    updated = await service.update_subscription(
        billing_context.tenant_id,
        auto_renew=False,
        seat_count=3,
        billing_email="billing@example.com",
    )

    assert updated.auto_renew is False
    assert updated.seat_count == 3
    assert updated.billing_email == "billing@example.com"


@pytest.mark.asyncio
async def test_record_usage_logs_entry(billing_context):
    service = _service(billing_context)

    await service.start_subscription(
        tenant_id=billing_context.tenant_id,
        plan_code="starter",
        billing_email="owner@example.com",
        auto_renew=True,
    )

    await service.record_usage(
        billing_context.tenant_id,
        feature_key="messages",
        quantity=5,
        idempotency_key="usage-1",
    )

    async with billing_context.session_factory() as session:
        rows = await session.execute(select(persistence_models.SubscriptionUsage))
        usage = rows.scalar_one()
        assert usage.quantity == 5


@pytest.mark.asyncio
async def test_gateway_errors_surface_as_payment_provider_error(billing_context):
    service = BillingService(billing_context.repository, ErrorGateway())

    with pytest.raises(PaymentProviderError):
        await service.start_subscription(
            tenant_id=billing_context.tenant_id,
            plan_code="starter",
            billing_email=None,
            auto_renew=True,
        )
