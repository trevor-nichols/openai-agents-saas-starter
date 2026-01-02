from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from typing import AsyncGenerator, Generator

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.domain.billing import SubscriptionInvoiceRecord
from app.infrastructure.persistence.billing.invoice_store import InvoiceStore
from app.infrastructure.persistence.billing.models import (
    BillingPlan,
    TenantSubscription,
)
from app.infrastructure.persistence.billing.usage_store import UsageStore
from app.infrastructure.persistence.models.base import Base
from app.infrastructure.persistence.tenants.models import TenantAccount


@pytest.fixture(scope="module")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
async def session_factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    engine: AsyncEngine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


async def _seed_subscription(
    session_factory: async_sessionmaker[AsyncSession],
) -> tuple[str, uuid.UUID]:
    tenant_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    subscription_id = uuid.uuid4()

    async with session_factory() as session:
        tenant = TenantAccount(id=tenant_id, slug="acme", name="Acme Corp")
        plan = BillingPlan(
            id=plan_id,
            code="starter",
            name="Starter",
            interval="monthly",
            interval_count=1,
            price_cents=1500,
            currency="USD",
            trial_days=14,
            seat_included=1,
            feature_toggles={},
            is_active=True,
        )
        subscription = TenantSubscription(
            id=subscription_id,
            tenant_id=tenant_id,
            plan_id=plan_id,
            status="active",
            auto_renew=True,
            billing_email="billing@example.com",
            processor="stripe",
            processor_customer_id="cus_123",
            processor_subscription_id="sub_123",
            starts_at=datetime(2025, 1, 1, tzinfo=UTC),
            current_period_start=datetime(2025, 1, 1, tzinfo=UTC),
            current_period_end=datetime(2025, 1, 31, tzinfo=UTC),
            trial_ends_at=None,
            cancel_at=None,
            seat_count=3,
            metadata_json={},
        )
        session.add_all([tenant, plan, subscription])
        await session.commit()

    return str(tenant_id), subscription_id


@pytest.mark.asyncio
async def test_usage_store_aggregates_by_feature(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id, _ = await _seed_subscription(session_factory)
    store = UsageStore(session_factory)

    await store.record_usage(
        tenant_id,
        feature_key="messages",
        quantity=5,
        period_start=datetime(2025, 1, 1, tzinfo=UTC),
        period_end=datetime(2025, 1, 31, tzinfo=UTC),
        idempotency_key="evt-1",
    )
    await store.record_usage(
        tenant_id,
        feature_key="messages",
        quantity=7,
        period_start=datetime(2025, 2, 1, tzinfo=UTC),
        period_end=datetime(2025, 2, 28, tzinfo=UTC),
        idempotency_key="evt-2",
    )
    await store.record_usage(
        tenant_id,
        feature_key="tokens",
        quantity=100,
        period_start=datetime(2025, 1, 1, tzinfo=UTC),
        period_end=datetime(2025, 1, 31, tzinfo=UTC),
        idempotency_key="evt-3",
    )
    await store.record_usage(
        tenant_id,
        feature_key="messages",
        quantity=5,
        period_start=datetime(2025, 1, 1, tzinfo=UTC),
        period_end=datetime(2025, 1, 31, tzinfo=UTC),
        idempotency_key="evt-1",
    )

    totals = await store.get_usage_totals(tenant_id, feature_keys=["messages"])

    assert len(totals) == 1
    assert totals[0].feature_key == "messages"
    assert totals[0].quantity == 12

    filtered = await store.get_usage_totals(
        tenant_id,
        feature_keys=["messages"],
        period_start=datetime(2025, 2, 1, tzinfo=UTC),
    )

    assert len(filtered) == 1
    assert filtered[0].quantity == 7


@pytest.mark.asyncio
async def test_invoice_store_upsert_updates_existing(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id, _ = await _seed_subscription(session_factory)
    store = InvoiceStore(session_factory)

    invoice = SubscriptionInvoiceRecord(
        tenant_id=tenant_id,
        period_start=datetime(2025, 1, 1, tzinfo=UTC),
        period_end=datetime(2025, 1, 31, tzinfo=UTC),
        amount_cents=2500,
        currency="USD",
        status="open",
        processor_invoice_id="inv_123",
        hosted_invoice_url="https://example.com/invoice/123",
    )

    await store.upsert_invoice(invoice)
    fetched = await store.get_invoice(tenant_id, invoice_id="inv_123")

    assert fetched is not None
    assert fetched.status == "open"
    assert fetched.amount_cents == 2500

    updated = SubscriptionInvoiceRecord(
        tenant_id=tenant_id,
        period_start=invoice.period_start,
        period_end=invoice.period_end,
        amount_cents=3000,
        currency="USD",
        status="paid",
        processor_invoice_id="inv_123",
        hosted_invoice_url="https://example.com/invoice/123",
    )

    await store.upsert_invoice(updated)
    refreshed = await store.get_invoice(tenant_id, invoice_id="inv_123")

    assert refreshed is not None
    assert refreshed.status == "paid"
    assert refreshed.amount_cents == 3000
