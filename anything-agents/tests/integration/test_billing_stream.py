"""Integration tests for the billing stream SSE endpoint."""

from __future__ import annotations

import asyncio

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies.auth import require_current_user
from app.api.v1.billing.router import router as billing_router
from app.core.config import get_settings
from app.services.billing_events import BillingEventsService, billing_events_service
from tests.utils.fake_billing_backend import QueueBillingEventBackend

pytestmark = pytest.mark.stripe_replay


@pytest.fixture(autouse=True)
def enable_stream(monkeypatch):
    monkeypatch.setenv("ENABLE_BILLING", "true")
    monkeypatch.setenv("ENABLE_BILLING_STREAM", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_sse_emits_events(monkeypatch):
    service = BillingEventsService()
    backend = QueueBillingEventBackend()
    service.configure(backend=backend, repository=None)

    monkeypatch.setattr("app.services.billing_events._billing_events_service", service, raising=False)
    monkeypatch.setattr("app.services.billing_events.billing_events_service", service, raising=False)

    app = FastAPI()
    app.dependency_overrides[require_current_user] = lambda: {"sub": "tester"}
    app.include_router(billing_router, prefix="/api/v1")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        async with client.stream(
            "GET",
            "/api/v1/billing/stream",
            headers={"X-Tenant-Id": "tenant-123", "X-Tenant-Role": "owner"},
        ) as response:
            assert response.status_code == 200

            await service.publish_raw(
                "tenant-123",
                {
                    "tenant_id": "tenant-123",
                    "event_type": "invoice.paid",
                    "stripe_event_id": "evt_stream",
                    "occurred_at": "2025-11-07T00:00:00Z",
                    "summary": "Invoice paid",
                    "status": "processed",
                },
            )

            collected = ""
            async for chunk in response.aiter_text():
                collected += chunk
                if "data:" in collected:
                    break
            assert "invoice.paid" in collected
