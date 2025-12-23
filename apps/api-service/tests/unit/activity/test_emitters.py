from __future__ import annotations

from types import SimpleNamespace
from typing import cast
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from sqlalchemy import delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.persistence.activity import models as _activity_models  # noqa: F401
from app.infrastructure.persistence.auth import models as _auth_models  # noqa: F401
from app.infrastructure.persistence.containers.models import AgentContainer, Container
from app.infrastructure.persistence.tenants.models import TenantAccount
from app.infrastructure.persistence.models.base import Base
from app.infrastructure.persistence.stripe.models import StripeEvent
from openai import AsyncOpenAI
from app.services.billing.billing_events.payloads import (
    BillingEventInvoice,
    BillingEventPayload,
    BillingEventSubscription,
)
from app.services.billing.billing_events.publisher import BillingEventPublisher
from app.services.billing.billing_events.protocols import BillingEventBackend
from app.services.containers.service import ContainerService
from app.services.vector_stores.sync_worker import OpenAIClientFactory, VectorStoreSyncWorker
from app.core.settings import get_settings


class _StubBackend(BillingEventBackend):
    def __init__(self) -> None:
        self.published: list[tuple[str, str]] = []
        self.subscribed = False

    async def publish(self, channel: str, message: str) -> None:
        self.published.append((channel, message))

    async def subscribe(self, channel: str):
        self.subscribed = True

        class _Stream:
            async def next_message(self, timeout: float | None = None) -> str | None:
                return None

            async def close(self) -> None:
                return None

        return _Stream()

    async def store_bookmark(self, key: str, value: str) -> None:
        return None

    async def load_bookmark(self, key: str) -> str | None:
        return None

    async def close(self) -> None:
        return None


@pytest.mark.asyncio
async def test_billing_publisher_records_activity(monkeypatch) -> None:
    message = BillingEventPayload(
        tenant_id="tenant-1",
        event_type="invoice.paid",
        stripe_event_id="evt_1",
        occurred_at="2025-12-01T00:00:00Z",
        summary="paid",
        status="paid",
        subscription=BillingEventSubscription(
            plan_code="pro",
            status="active",
            seat_count=5,
            auto_renew=True,
            current_period_start=None,
            current_period_end=None,
            trial_ends_at=None,
            cancel_at=None,
        ),
        invoice=BillingEventInvoice(
            invoice_id="inv_1",
            status="paid",
            amount_due_cents=1200,
            currency="usd",
            billing_reason=None,
            hosted_invoice_url=None,
            collection_method=None,
            period_start=None,
            period_end=None,
        ),
    )
    normalizer = Mock()
    normalizer.normalize = Mock(return_value=message)
    backend = _StubBackend()
    publisher = BillingEventPublisher(normalizer=normalizer)
    publisher.configure(backend=cast(BillingEventBackend, backend))

    record_mock = AsyncMock()
    monkeypatch.setattr(
        "app.services.billing.billing_events.publisher.activity_service",
        SimpleNamespace(record=record_mock),
    )

    record = MagicMock(spec=StripeEvent)
    record.event_type = "invoice.paid"
    record.stripe_event_id = "evt_1"
    record.tenant_hint = "tenant-1"
    await publisher._publish(record, {}, None, source="webhook")

    assert backend.published
    assert record_mock.await_count == 2
    sub_call, invoice_call = record_mock.await_args_list
    assert sub_call.kwargs["action"] == "billing.subscription.updated"
    assert invoice_call.kwargs["action"] == "billing.invoice.paid"
    assert invoice_call.kwargs["status"] == "success"


@pytest.mark.asyncio
async def test_vector_sync_worker_records_activity(monkeypatch) -> None:
    session_factory = cast(async_sessionmaker[AsyncSession], AsyncMock())

    def _client_factory(_: UUID) -> AsyncOpenAI:
        return cast(AsyncOpenAI, MagicMock(spec=AsyncOpenAI))

    client_factory: OpenAIClientFactory = cast(OpenAIClientFactory, _client_factory)

    worker = VectorStoreSyncWorker(
        session_factory=session_factory,
        settings_factory=get_settings,
        client_factory=client_factory,
    )
    record_mock = AsyncMock()
    monkeypatch.setattr(
        "app.services.vector_stores.sync_worker.activity_service.record", record_mock
    )

    await worker._record_activity(
        tenant_id="tenant-1",
        vector_store_id="vs-1",
        file_id="file-1",
        state="failed",
    )

    record_mock.assert_awaited_once()
    assert record_mock.await_args is not None
    kwargs = record_mock.await_args.kwargs
    assert kwargs["status"] == "failure"
    assert kwargs["metadata"]["state"] == "failed"


@pytest.mark.asyncio
async def test_container_bind_and_unbind_record_activity(monkeypatch) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        engine, expire_on_commit=False
    )

    tenant_id = uuid4()
    container_id = uuid4()
    async with session_factory() as session:
        session.add(TenantAccount(id=tenant_id, slug="tenant", name="Tenant"))
        session.add(
            Container(
                id=container_id,
                openai_id="c-1",
                tenant_id=tenant_id,
                owner_user_id=None,
                name="demo",
                memory_limit="1g",
                status="running",
                metadata_json={},
            )
        )
        await session.commit()

    settings = get_settings()
    settings.container_allowed_memory_tiers = ["1g"]
    settings.container_default_auto_memory = "1g"
    settings.container_max_containers_per_tenant = 5
    service = ContainerService(session_factory, lambda: settings)

    record_mock = AsyncMock()
    monkeypatch.setattr(
        "app.services.containers.service.activity_service", SimpleNamespace(record=record_mock)
    )

    await service.bind_agent(
        tenant_id=tenant_id,
        agent_key="triage",
        container_id=container_id,
    )
    record_mock.assert_awaited()
    assert record_mock.await_args is not None
    kwargs = record_mock.await_args.kwargs
    assert kwargs["metadata"]["event"] == "bound"

    record_mock.reset_mock()
    await service.unbind_agent(tenant_id=tenant_id, agent_key="triage")
    record_mock.assert_awaited()
    assert record_mock.await_args is not None
    kwargs = record_mock.await_args.kwargs
    assert kwargs["metadata"]["event"] == "unbound"

    async with session_factory() as session:
        await session.execute(sa_delete(AgentContainer))
        await session.execute(sa_delete(Container))
        await session.commit()

    await engine.dispose()
