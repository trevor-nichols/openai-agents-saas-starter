"""Integration tests for the billing stream SSE endpoint."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient

from app.api.dependencies.auth import require_current_user
from app.api.v1.billing.router import router as billing_router
from app.bootstrap import get_container
from app.core.settings import get_settings
from app.infrastructure.persistence.stripe.models import StripeEvent, StripeEventStatus
from app.services.billing.billing_events import (
    BillingEventHistoryPage,
    BillingEventPayload,
    BillingEventsService,
)
from app.services.billing.stripe.event_models import (
    DispatchBroadcastContext,
    InvoiceSnapshotView,
    SubscriptionSnapshotView,
    UsageDelta,
)
from tests.utils.fake_billing_backend import QueueBillingEventBackend

TEST_TENANT_ID = str(uuid4())

pytestmark = pytest.mark.stripe_replay


@pytest.fixture(autouse=True)
def enable_stream(monkeypatch):
    monkeypatch.setenv("ENABLE_BILLING", "true")
    monkeypatch.setenv("ENABLE_BILLING_STREAM", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def stub_billing_events_service():
    service = BillingEventsService()
    backend = QueueBillingEventBackend()
    service.configure(backend=backend, repository=None)
    container = get_container()
    original_service = container.billing_events_service
    container.billing_events_service = service
    try:
        yield service, backend
    finally:
        container.billing_events_service = original_service


@pytest.mark.asyncio
async def test_sse_emits_events(stub_billing_events_service):
    service, backend = stub_billing_events_service
    app = FastAPI()
    app.dependency_overrides[require_current_user] = _authorized_user
    app.include_router(billing_router, prefix="/api/v1")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        async with client.stream(
            "GET",
            "/api/v1/billing/stream",
            headers={"X-Tenant-Id": TEST_TENANT_ID, "X-Tenant-Role": "owner"},
        ) as response:
            assert response.status_code == 200

            await _publish_invoice_event(service, TEST_TENANT_ID)

            collected = ""
            async for chunk in response.aiter_text():
                collected += chunk
                if "data:" in collected:
                    break
            payload = _extract_event_payload(collected)
            assert payload["event_type"] == "invoice.payment_succeeded"
            assert payload["subscription"]["plan_code"] == "starter"
            assert payload["invoice"]["status"] == "paid"
            assert payload["usage"][0]["feature_key"] == "messages"


@pytest.mark.asyncio
async def test_stream_rejects_tenant_mismatch(stub_billing_events_service):
    service, _ = stub_billing_events_service

    app = FastAPI()
    app.dependency_overrides[require_current_user] = _authorized_user
    app.include_router(billing_router, prefix="/api/v1")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/api/v1/billing/stream",
            headers={"X-Tenant-Id": str(uuid4()), "X-Tenant-Role": "owner"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_context_tenant_override_publishes_to_correct_channel(
    stub_billing_events_service,
):
    service, backend = stub_billing_events_service

    # Event lacks tenant_hint but dispatcher context resolves the tenant.
    now = datetime.now(UTC)
    record = StripeEvent(
        id=uuid4(),
        stripe_event_id="evt_missing_hint",
        event_type="invoice.payment_succeeded",
        payload={"data": {"object": {"status": "paid"}}},
        tenant_hint=None,
        stripe_created_at=now,
        received_at=now,
        processed_at=now,
        processing_outcome=StripeEventStatus.PROCESSED.value,
        processing_attempts=1,
    )
    override_tenant = "tenant-override"
    context = DispatchBroadcastContext(
        tenant_id=override_tenant,
        event_type="invoice.payment_succeeded",
        summary="Invoice paid",
        status="paid",
        subscription=None,
        invoice=None,
        usage=[],
    )

    await service.publish_from_event(record, record.payload, context=context)

    published = backend.pop(override_tenant)
    assert published is not None, "Expected message in override tenant channel"
    payload = json.loads(published)
    assert payload["tenant_id"] == override_tenant
    assert payload["event_type"] == "invoice.payment_succeeded"


@pytest.mark.asyncio
async def test_history_endpoint_returns_events(stub_billing_events_service):
    service, _ = stub_billing_events_service
    original = service.list_history
    sample_event = BillingEventPayload(
        tenant_id=TEST_TENANT_ID,
        event_type="invoice.payment_succeeded",
        stripe_event_id="evt_history",
        occurred_at=datetime.now(UTC).isoformat(),
        summary="Invoice paid",
        status="processed",
        subscription=None,
        invoice=None,
        usage=[],
    )
    service.list_history = AsyncMock(
        return_value=BillingEventHistoryPage(items=[sample_event], next_cursor=None)
    )

    app = FastAPI()
    app.dependency_overrides[require_current_user] = _authorized_user
    app.include_router(billing_router, prefix="/api/v1")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            f"/api/v1/billing/tenants/{TEST_TENANT_ID}/events",
            headers={"X-Tenant-Id": TEST_TENANT_ID, "X-Tenant-Role": "owner"},
        )

    service.list_history = original

    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["stripe_event_id"] == "evt_history"


async def _publish_invoice_event(service: BillingEventsService, tenant_id: str) -> None:
    now = datetime.now(UTC)
    record = StripeEvent(
        id=uuid4(),
        stripe_event_id="evt_stream",
        event_type="invoice.payment_succeeded",
        payload={"data": {"object": {"status": "paid"}}},
        tenant_hint=tenant_id,
        stripe_created_at=now,
        received_at=now,
        processed_at=now,
        processing_outcome=StripeEventStatus.PROCESSED.value,
        processing_attempts=1,
    )
    context = DispatchBroadcastContext(
        tenant_id=tenant_id,
        event_type="invoice.payment_succeeded",
        summary="Invoice paid",
        status="paid",
        subscription=SubscriptionSnapshotView(
            tenant_id=tenant_id,
            plan_code="starter",
            status="active",
            auto_renew=True,
            seat_count=5,
            current_period_start=now,
            current_period_end=now,
            trial_ends_at=None,
            cancel_at=None,
        ),
        invoice=InvoiceSnapshotView(
            tenant_id=tenant_id,
            invoice_id="in_test",
            status="paid",
            amount_due_cents=1200,
            currency="usd",
            billing_reason="subscription_cycle",
            hosted_invoice_url="https://example.com",
            collection_method="charge_automatically",
            period_start=now,
            period_end=now,
        ),
        usage=[
            UsageDelta(
                feature_key="messages",
                quantity=42,
                period_start=now,
                period_end=now,
                idempotency_key="line-1",
                amount_cents=300,
            )
        ],
    )
    await service.publish_from_event(record, record.payload, context=context)


def _extract_event_payload(stream_buffer: str) -> dict[str, Any]:
    for block in stream_buffer.split("\n\n"):
        if block.startswith("data:"):
            raw = block.replace("data:", "", 1).strip()
            return json.loads(raw)
    raise AssertionError("No SSE data payload found")


def _authorized_user():
    return {
        "user_id": "tester",
        "subject": "user:tester",
        "payload": {
            "tenant_id": TEST_TENANT_ID,
            "roles": ["owner"],
            "scope": "billing:manage billing:read",
        },
    }
