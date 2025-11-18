"""Tests covering the billing service scaffolding."""

import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import cast

import pytest
from sqlalchemy import Table, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.persistence.auth import models as auth_models  # noqa: F401
from app.infrastructure.persistence.billing import models as billing_models
from app.infrastructure.persistence.billing.postgres import PostgresBillingRepository
from app.infrastructure.persistence.conversations import models as conversation_models
from app.infrastructure.persistence.tenants import models as tenant_models
from app.services.billing.billing_service import (
    BillingService,
    PaymentProviderError,
    ProcessorInvoiceLineSnapshot,
    ProcessorInvoiceSnapshot,
)
from app.services.billing.payment_gateway import (
    PaymentGateway,
    PaymentGatewayError,
    SubscriptionProvisionResult,
)
from tests.utils.sqlalchemy import create_tables


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
        trial_days: int | None,
    ) -> SubscriptionProvisionResult:
        self.subscription_counter += 1
        now = datetime.now(UTC)
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
    async def start_subscription(
        self,
        *,
        tenant_id: str,
        plan_code: str,
        billing_email: str | None,
        auto_renew: bool,
        seat_count: int | None,
        trial_days: int | None,
    ) -> SubscriptionProvisionResult:
        raise PaymentGatewayError("boom")


TABLES_TO_CREATE = cast(
    tuple[Table, ...],
    (
        conversation_models.TenantAccount.__table__,
        tenant_models.TenantSettingsModel.__table__,
        billing_models.BillingPlan.__table__,
        billing_models.PlanFeature.__table__,
        billing_models.TenantSubscription.__table__,
        billing_models.SubscriptionInvoice.__table__,
        billing_models.SubscriptionUsage.__table__,
    ),
)


@pytest.fixture
async def billing_context():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(lambda connection: create_tables(connection, TABLES_TO_CREATE))

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    tenant_id = uuid.uuid4()

    async with session_factory() as session:
        session.add(
            conversation_models.TenantAccount(
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
    starter = billing_models.BillingPlan(
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
    pro = billing_models.BillingPlan(
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
        trial_days=None,
    )

    assert subscription.processor_subscription_id is not None

    stored = await service.get_subscription(billing_context.tenant_id)
    assert stored is not None
    assert stored.plan_code == "starter"


@pytest.mark.asyncio
async def test_ingest_invoice_snapshot_records_invoice_and_usage(billing_context):
    service = _service(billing_context)

    await service.start_subscription(
        tenant_id=billing_context.tenant_id,
        plan_code="starter",
        billing_email="owner@example.com",
        auto_renew=True,
        trial_days=None,
    )

    now = datetime.now(UTC)
    snapshot = ProcessorInvoiceSnapshot(
        tenant_id=billing_context.tenant_id,
        invoice_id="in_local",
        status="paid",
        amount_due_cents=1500,
        currency="usd",
        period_start=now,
        period_end=now,
        hosted_invoice_url="https://example.com",
        billing_reason="subscription_cycle",
        collection_method="charge_automatically",
        description="Monthly",
        lines=[
            ProcessorInvoiceLineSnapshot(
                feature_key="messages",
                quantity=5,
                period_start=now,
                period_end=now,
                idempotency_key="line_1",
                amount_cents=500,
            )
        ],
    )

    await service.ingest_invoice_snapshot(snapshot)

    async with billing_context.session_factory() as session:
        invoice = await session.scalar(
            select(billing_models.SubscriptionInvoice).where(
                billing_models.SubscriptionInvoice.external_invoice_id == "in_local"
            )
        )
        assert invoice is not None
        usage = await session.scalar(select(billing_models.SubscriptionUsage))
        assert usage is not None
        assert usage.quantity == 5


@pytest.mark.asyncio
async def test_update_subscription_applies_changes(billing_context):
    gateway = FakeGateway()
    service = BillingService(billing_context.repository, gateway)

    await service.start_subscription(
        tenant_id=billing_context.tenant_id,
        plan_code="starter",
        billing_email="owner@example.com",
        auto_renew=True,
        trial_days=None,
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
        trial_days=None,
    )

    await service.record_usage(
        billing_context.tenant_id,
        feature_key="messages",
        quantity=5,
        idempotency_key="usage-1",
    )

    async with billing_context.session_factory() as session:
        rows = await session.execute(select(billing_models.SubscriptionUsage))
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
            trial_days=None,
        )


@pytest.mark.asyncio
async def test_get_usage_totals_returns_windowed_sums(billing_context):
    service = _service(billing_context)
    await service.start_subscription(
        tenant_id=billing_context.tenant_id,
        plan_code="starter",
        billing_email="billing@example.com",
        auto_renew=True,
        seat_count=None,
        trial_days=None,
    )

    window_start = datetime(2025, 1, 1, tzinfo=UTC)
    window_end = datetime(2025, 1, 31, tzinfo=UTC)

    await billing_context.repository.record_usage(
        billing_context.tenant_id,
        feature_key="messages",
        quantity=5,
        period_start=window_start,
        period_end=window_start + timedelta(days=1),
        idempotency_key="usage-1",
    )
    await billing_context.repository.record_usage(
        billing_context.tenant_id,
        feature_key="messages",
        quantity=3,
        period_start=window_start + timedelta(days=2),
        period_end=window_start + timedelta(days=3),
        idempotency_key="usage-2",
    )
    await billing_context.repository.record_usage(
        billing_context.tenant_id,
        feature_key="messages",
        quantity=2,
        period_start=window_end + timedelta(days=1),
        period_end=window_end + timedelta(days=2),
        idempotency_key="usage-3",
    )

    totals = await billing_context.repository.get_usage_totals(
        billing_context.tenant_id,
        feature_keys=["messages"],
        period_start=window_start,
        period_end=window_end,
    )

    assert len(totals) == 1
    total = totals[0]
    assert total.feature_key == "messages"
    assert total.quantity == 8
    assert total.window_start == window_start
    assert total.window_end == window_end


@pytest.mark.asyncio
async def test_get_usage_totals_handles_multiple_features(billing_context):
    service = _service(billing_context)
    await service.start_subscription(
        tenant_id=billing_context.tenant_id,
        plan_code="starter",
        billing_email="billing@example.com",
        auto_renew=True,
        seat_count=None,
        trial_days=None,
    )

    base = datetime(2025, 2, 1, tzinfo=UTC)

    await billing_context.repository.record_usage(
        billing_context.tenant_id,
        feature_key="messages",
        quantity=4,
        period_start=base,
        period_end=base + timedelta(days=1),
        idempotency_key="multi-1",
    )
    await billing_context.repository.record_usage(
        billing_context.tenant_id,
        feature_key="output_tokens",
        quantity=750,
        period_start=base,
        period_end=base + timedelta(days=1),
        idempotency_key="multi-2",
    )

    totals = await billing_context.repository.get_usage_totals(
        billing_context.tenant_id,
        period_start=base,
        period_end=base + timedelta(days=30),
    )

    assert {t.feature_key for t in totals} == {"messages", "output_tokens"}
    totals_map = {t.feature_key: t for t in totals}
    assert totals_map["messages"].quantity == 4
    assert totals_map["output_tokens"].quantity == 750
