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
from app.infrastructure.persistence.tenants import models as tenant_models
from app.services.billing.billing_service import (
    BillingService,
    InvalidTenantIdentifierError,
    PlanChangeTiming,
    PaymentProviderError,
    ProcessorInvoiceLineSnapshot,
    ProcessorInvoiceSnapshot,
    ProcessorSubscriptionSnapshot,
    SubscriptionStateError,
)
from app.domain.billing import BillingCustomerRecord, TenantSubscription
from app.services.billing.payment_gateway import (
    CustomerProvisionResult,
    PaymentGateway,
    PaymentGatewayError,
    PaymentMethodSummary,
    PortalSessionResult,
    SetupIntentResult,
    SubscriptionProvisionResult,
    SubscriptionPlanScheduleResult,
    SubscriptionPlanSwapResult,
    UpcomingInvoicePreviewResult,
)
from tests.utils.sqlalchemy import create_tables


class FakeGateway(PaymentGateway):
    """Stub gateway used for service tests."""

    def __init__(self) -> None:
        self.subscription_counter = 0
        self.last_quantity: int | None = None
        self.usage_records: list[dict[str, object]] = []
        self.created_customers: list[CustomerProvisionResult] = []
        self.last_billing_email: str | None = None
        self.plan_swaps: list[dict[str, object]] = []
        self.plan_schedules: list[dict[str, object]] = []

    async def start_subscription(
        self,
        *,
        tenant_id: str,
        plan_code: str,
        billing_email: str | None,
        auto_renew: bool,
        seat_count: int | None,
        trial_days: int | None,
        customer_id: str | None = None,
    ) -> SubscriptionProvisionResult:
        self.subscription_counter += 1
        now = datetime.now(UTC)
        self.last_quantity = seat_count or 1
        self.last_billing_email = billing_email
        return SubscriptionProvisionResult(
            processor="stripe",
            customer_id=customer_id or f"cust_{tenant_id}",
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

    async def create_customer(
        self, *, tenant_id: str, billing_email: str | None
    ) -> CustomerProvisionResult:
        result = CustomerProvisionResult(
            processor="stripe",
            customer_id=f"cust_{tenant_id}",
            billing_email=billing_email,
        )
        self.created_customers.append(result)
        return result

    async def create_portal_session(
        self, *, customer_id: str, return_url: str
    ) -> PortalSessionResult:
        return PortalSessionResult(url="https://portal.example.com")

    async def list_payment_methods(self, *, customer_id: str):
        return [
            PaymentMethodSummary(
                id="pm_123",
                brand="visa",
                last4="4242",
                exp_month=12,
                exp_year=2030,
                is_default=True,
            )
        ]

    async def create_setup_intent(self, *, customer_id: str):
        return SetupIntentResult(id="seti_123", client_secret="secret")

    async def set_default_payment_method(
        self, *, customer_id: str, payment_method_id: str
    ) -> None:
        return None

    async def detach_payment_method(
        self, *, customer_id: str, payment_method_id: str
    ) -> None:
        return None

    async def preview_upcoming_invoice(
        self,
        *,
        subscription_id: str,
        seat_count: int | None,
        proration_behavior: str | None = None,
    ) -> UpcomingInvoicePreviewResult:
        now = datetime.now(UTC)
        return UpcomingInvoicePreviewResult(
            invoice_id="in_123",
            amount_due_cents=1200,
            currency="usd",
            period_start=now,
            period_end=now,
            lines=[],
        )

    async def swap_subscription_plan(
        self,
        subscription_id: str,
        *,
        plan_code: str,
        seat_count: int | None,
        schedule_id: str | None = None,
        proration_behavior: str | None = None,
    ) -> SubscriptionPlanSwapResult:
        self.plan_swaps.append(
            {
                "subscription_id": subscription_id,
                "plan_code": plan_code,
                "seat_count": seat_count,
                "schedule_id": schedule_id,
                "proration_behavior": proration_behavior,
            }
        )
        now = datetime.now(UTC)
        return SubscriptionPlanSwapResult(
            price_id="price_123",
            subscription_item_id="si_123",
            current_period_start=now,
            current_period_end=now,
            quantity=seat_count or 1,
            metadata={},
        )

    async def schedule_subscription_plan(
        self,
        subscription_id: str,
        *,
        plan_code: str,
        seat_count: int | None,
    ) -> SubscriptionPlanScheduleResult:
        self.plan_schedules.append(
            {
                "subscription_id": subscription_id,
                "plan_code": plan_code,
                "seat_count": seat_count,
            }
        )
        now = datetime.now(UTC)
        return SubscriptionPlanScheduleResult(
            schedule_id="sched_123",
            price_id="price_123",
            current_period_start=now,
            current_period_end=now,
            quantity=seat_count or 1,
            metadata={},
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
        customer_id: str | None = None,
    ) -> SubscriptionProvisionResult:
        raise PaymentGatewayError("boom")


TABLES_TO_CREATE = cast(
    tuple[Table, ...],
    (
        tenant_models.TenantAccount.__table__,
        tenant_models.TenantSettingsModel.__table__,
        billing_models.BillingPlan.__table__,
        billing_models.PlanFeature.__table__,
        billing_models.TenantSubscription.__table__,
        billing_models.BillingCustomer.__table__,
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
            tenant_models.TenantAccount(
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
async def test_start_subscription_defaults_seat_count_to_plan(billing_context):
    gateway = FakeGateway()
    service = BillingService(billing_context.repository, gateway)

    subscription = await service.start_subscription(
        tenant_id=billing_context.tenant_id,
        plan_code="pro",
        billing_email="owner@example.com",
        auto_renew=True,
        seat_count=None,
        trial_days=None,
    )

    assert subscription.seat_count == 5
    assert gateway.last_quantity == 5


@pytest.mark.asyncio
async def test_start_subscription_reuses_existing_billing_email(billing_context):
    gateway = FakeGateway()
    service = BillingService(billing_context.repository, gateway)

    await billing_context.repository.upsert_customer(
        BillingCustomerRecord(
            tenant_id=billing_context.tenant_id,
            processor="stripe",
            processor_customer_id="cus_existing",
            billing_email="billing@example.com",
        )
    )

    subscription = await service.start_subscription(
        tenant_id=billing_context.tenant_id,
        plan_code="starter",
        billing_email=None,
        auto_renew=True,
        trial_days=None,
    )

    assert subscription.billing_email == "billing@example.com"
    assert subscription.processor_customer_id == "cus_existing"
    assert gateway.last_billing_email == "billing@example.com"

    customer = await billing_context.repository.get_customer(
        billing_context.tenant_id,
        processor="stripe",
    )
    assert customer is not None
    assert customer.billing_email == "billing@example.com"


@pytest.mark.asyncio
async def test_resolve_customer_does_not_clear_existing_email(billing_context):
    gateway = FakeGateway()
    service = BillingService(billing_context.repository, gateway)

    await billing_context.repository.upsert_customer(
        BillingCustomerRecord(
            tenant_id=billing_context.tenant_id,
            processor="stripe",
            processor_customer_id="cus_existing",
            billing_email="billing@example.com",
        )
    )

    now = datetime.now(UTC)
    await billing_context.repository.upsert_subscription(
        TenantSubscription(
            tenant_id=billing_context.tenant_id,
            plan_code="starter",
            status="active",
            auto_renew=True,
            billing_email=None,
            starts_at=now,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            seat_count=1,
            metadata={},
            processor="stripe",
            processor_customer_id="cus_existing",
            processor_subscription_id="sub_existing",
        )
    )

    await service.list_payment_methods(billing_context.tenant_id)

    customer = await billing_context.repository.get_customer(
        billing_context.tenant_id,
        processor="stripe",
    )
    assert customer is not None
    assert customer.billing_email == "billing@example.com"


@pytest.mark.asyncio
async def test_get_subscription_invalid_tenant_raises(billing_context):
    service = _service(billing_context)

    with pytest.raises(InvalidTenantIdentifierError):
        await service.get_subscription("not-a-uuid")


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


@pytest.mark.asyncio
async def test_create_setup_intent_creates_customer_record(billing_context):
    service = _service(billing_context)

    await service.create_setup_intent(
        billing_context.tenant_id,
        billing_email="billing@example.com",
    )

    customer = await billing_context.repository.get_customer(
        billing_context.tenant_id, processor="stripe"
    )
    assert customer is not None
    assert customer.billing_email == "billing@example.com"


@pytest.mark.asyncio
async def test_preview_upcoming_invoice_includes_plan_name(billing_context):
    service = _service(billing_context)
    await service.start_subscription(
        tenant_id=billing_context.tenant_id,
        plan_code="starter",
        billing_email="owner@example.com",
        auto_renew=True,
        trial_days=None,
    )

    preview = await service.preview_upcoming_invoice(
        billing_context.tenant_id,
        seat_count=None,
    )

    assert preview.plan_code == "starter"
    assert preview.plan_name == "Starter"


@pytest.mark.asyncio
async def test_change_subscription_plan_updates_plan(billing_context):
    gateway = FakeGateway()
    service = BillingService(billing_context.repository, gateway)

    await service.start_subscription(
        tenant_id=billing_context.tenant_id,
        plan_code="starter",
        billing_email="owner@example.com",
        auto_renew=True,
        trial_days=None,
    )

    result = await service.change_subscription_plan(
        tenant_id=billing_context.tenant_id,
        plan_code="pro",
    )

    assert result.subscription.plan_code == "pro"
    assert result.subscription.pending_plan_code is None
    assert result.target_plan_code == "pro"
    assert result.timing == PlanChangeTiming.IMMEDIATE
    assert gateway.plan_swaps[0]["plan_code"] == "pro"


@pytest.mark.asyncio
async def test_change_subscription_plan_rejects_same_plan(billing_context):
    service = _service(billing_context)

    await service.start_subscription(
        tenant_id=billing_context.tenant_id,
        plan_code="starter",
        billing_email="owner@example.com",
        auto_renew=True,
        trial_days=None,
    )

    with pytest.raises(SubscriptionStateError):
        await service.change_subscription_plan(
            tenant_id=billing_context.tenant_id,
            plan_code="starter",
        )


@pytest.mark.asyncio
async def test_change_subscription_plan_updates_seat_count(billing_context):
    gateway = FakeGateway()
    service = BillingService(billing_context.repository, gateway)

    await service.start_subscription(
        tenant_id=billing_context.tenant_id,
        plan_code="starter",
        billing_email="owner@example.com",
        auto_renew=True,
        trial_days=None,
    )

    result = await service.change_subscription_plan(
        tenant_id=billing_context.tenant_id,
        plan_code="pro",
        seat_count=4,
    )

    assert result.subscription.seat_count == 4
    assert gateway.plan_swaps[0]["seat_count"] == 4


@pytest.mark.asyncio
async def test_change_subscription_plan_schedules_downgrade(billing_context):
    gateway = FakeGateway()
    service = BillingService(billing_context.repository, gateway)

    await service.start_subscription(
        tenant_id=billing_context.tenant_id,
        plan_code="pro",
        billing_email="owner@example.com",
        auto_renew=True,
        trial_days=None,
    )

    result = await service.change_subscription_plan(
        tenant_id=billing_context.tenant_id,
        plan_code="starter",
    )

    assert result.subscription.plan_code == "pro"
    assert result.subscription.pending_plan_code == "starter"
    assert result.subscription.pending_seat_count is not None
    assert result.timing == PlanChangeTiming.PERIOD_END
    assert result.subscription.pending_plan_effective_at == result.effective_at
    assert gateway.plan_schedules[0]["plan_code"] == "starter"


@pytest.mark.asyncio
async def test_change_subscription_plan_persists_pending_metadata(billing_context):
    gateway = FakeGateway()
    service = BillingService(billing_context.repository, gateway)

    await service.start_subscription(
        tenant_id=billing_context.tenant_id,
        plan_code="pro",
        billing_email="owner@example.com",
        auto_renew=True,
        trial_days=None,
    )

    result = await service.change_subscription_plan(
        tenant_id=billing_context.tenant_id,
        plan_code="starter",
        timing=PlanChangeTiming.PERIOD_END,
    )

    refreshed = await service.get_subscription(billing_context.tenant_id)
    assert refreshed is not None
    assert refreshed.pending_plan_code == "starter"
    assert refreshed.pending_seat_count == result.seat_count
    assert refreshed.processor_schedule_id == "sched_123"

    async with billing_context.session_factory() as session:
        tenant_uuid = uuid.UUID(billing_context.tenant_id)
        row = await session.scalar(
            select(billing_models.TenantSubscription).where(
                billing_models.TenantSubscription.tenant_id == tenant_uuid
            )
        )
        assert row is not None
        metadata = row.metadata_json or {}
        assert metadata.get("pending_plan_code") == "starter"
        assert metadata.get("processor_schedule_id") == "sched_123"


@pytest.mark.asyncio
async def test_change_subscription_plan_forces_period_end_for_upgrade(billing_context):
    gateway = FakeGateway()
    service = BillingService(billing_context.repository, gateway)

    await service.start_subscription(
        tenant_id=billing_context.tenant_id,
        plan_code="starter",
        billing_email="owner@example.com",
        auto_renew=True,
        trial_days=None,
    )

    result = await service.change_subscription_plan(
        tenant_id=billing_context.tenant_id,
        plan_code="pro",
        timing=PlanChangeTiming.PERIOD_END,
    )

    assert result.timing == PlanChangeTiming.PERIOD_END
    assert result.subscription.plan_code == "starter"
    assert result.subscription.pending_plan_code == "pro"
    assert result.subscription.pending_plan_effective_at == result.effective_at
    assert gateway.plan_schedules[0]["plan_code"] == "pro"


@pytest.mark.asyncio
async def test_change_subscription_plan_forces_immediate_for_downgrade(billing_context):
    gateway = FakeGateway()
    service = BillingService(billing_context.repository, gateway)

    await service.start_subscription(
        tenant_id=billing_context.tenant_id,
        plan_code="pro",
        billing_email="owner@example.com",
        auto_renew=True,
        trial_days=None,
    )

    result = await service.change_subscription_plan(
        tenant_id=billing_context.tenant_id,
        plan_code="starter",
        timing=PlanChangeTiming.IMMEDIATE,
    )

    assert result.timing == PlanChangeTiming.IMMEDIATE
    assert result.subscription.plan_code == "starter"
    assert result.subscription.pending_plan_code is None
    assert gateway.plan_swaps[0]["plan_code"] == "starter"


@pytest.mark.asyncio
async def test_sync_subscription_preserves_pending_plan_metadata(billing_context):
    service = _service(billing_context)

    subscription = await service.start_subscription(
        tenant_id=billing_context.tenant_id,
        plan_code="starter",
        billing_email="owner@example.com",
        auto_renew=True,
        trial_days=None,
    )
    subscription.pending_plan_code = "pro"
    subscription.processor_schedule_id = "sched_123"
    await billing_context.repository.upsert_subscription(subscription)

    snapshot = ProcessorSubscriptionSnapshot(
        tenant_id=billing_context.tenant_id,
        plan_code="starter",
        status="active",
        auto_renew=True,
        starts_at=subscription.starts_at,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        trial_ends_at=subscription.trial_ends_at,
        cancel_at=subscription.cancel_at,
        seat_count=subscription.seat_count,
        billing_email=subscription.billing_email,
        processor_customer_id=subscription.processor_customer_id,
        processor_subscription_id=subscription.processor_subscription_id or "sub_sync",
        processor_schedule_id="sched_123",
        metadata={
            "processor_price_id": "price_123",
            "processor_status": "active",
        },
    )

    synced = await service.sync_subscription_from_processor(snapshot)
    assert synced.pending_plan_code == "pro"
    assert synced.processor_schedule_id == "sched_123"


@pytest.mark.asyncio
async def test_sync_subscription_clears_pending_plan_if_schedule_removed(billing_context):
    service = _service(billing_context)

    subscription = await service.start_subscription(
        tenant_id=billing_context.tenant_id,
        plan_code="starter",
        billing_email="owner@example.com",
        auto_renew=True,
        trial_days=None,
    )
    subscription.pending_plan_code = "pro"
    subscription.processor_schedule_id = "sched_123"
    await billing_context.repository.upsert_subscription(subscription)

    snapshot = ProcessorSubscriptionSnapshot(
        tenant_id=billing_context.tenant_id,
        plan_code="starter",
        status="active",
        auto_renew=True,
        starts_at=subscription.starts_at,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        trial_ends_at=subscription.trial_ends_at,
        cancel_at=subscription.cancel_at,
        seat_count=subscription.seat_count,
        billing_email=subscription.billing_email,
        processor_customer_id=subscription.processor_customer_id,
        processor_subscription_id=subscription.processor_subscription_id or "sub_sync",
        processor_schedule_id=None,
        metadata={
            "processor_price_id": "price_123",
            "processor_status": "active",
        },
    )

    synced = await service.sync_subscription_from_processor(snapshot)
    assert synced.pending_plan_code is None
    assert synced.processor_schedule_id is None
