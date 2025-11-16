"""Integration tests for the Stripe webhook endpoint."""

from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator
from pathlib import Path
from typing import cast

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Table
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.bootstrap import get_container
from app.core.config import get_settings
from app.infrastructure.persistence.auth import models as auth_models
from app.infrastructure.persistence.conversations import models as conversation_models
from app.infrastructure.persistence.stripe.models import StripeEvent, StripeEventDispatch
from app.infrastructure.persistence.stripe.repository import (
    StripeEventRepository,
    StripeEventStatus,
    configure_stripe_event_repository,
    reset_stripe_event_repository,
)
from app.presentation.webhooks import stripe as stripe_webhook
from app.services.billing_events import BillingEventsService
from app.services.billing_service import BillingService
from app.services.stripe_dispatcher import stripe_event_dispatcher
from tests.utils.fake_billing_backend import QueueBillingEventBackend
from tests.utils.sqlalchemy import create_tables

_ = (auth_models, conversation_models)

pytestmark = pytest.mark.stripe_replay


@pytest.fixture(autouse=True)
def configure_secret(monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setenv("ENABLE_BILLING", "true")
    monkeypatch.setenv("ENABLE_BILLING_STREAM", "true")
    get_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()


class _FakeBillingService:
    def __init__(self) -> None:
        self.snapshot_calls: int = 0

    async def sync_subscription_from_processor(self, *_args, **_kwargs):
        self.snapshot_calls += 1


STRIPE_TABLES = cast(
    tuple[Table, ...],
    (
        StripeEvent.__table__,
        StripeEventDispatch.__table__,
    ),
)


@pytest.fixture
async def sqlite_stripe_repo() -> AsyncIterator[StripeEventRepository]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(lambda connection: create_tables(connection, STRIPE_TABLES))
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    repo = StripeEventRepository(session_factory)
    configure_stripe_event_repository(repo)
    fake_billing = _FakeBillingService()
    stripe_event_dispatcher.configure(
        repository=repo,
        billing=cast(BillingService, fake_billing),
    )
    try:
        yield repo
    finally:
        reset_stripe_event_repository()
        await engine.dispose()


@pytest.fixture
def webhook_app():
    app = FastAPI()
    app.include_router(stripe_webhook.router)
    return app


@pytest.fixture
def fake_billing_events():
    service = BillingEventsService()
    backend = QueueBillingEventBackend()
    service.configure(backend=backend, repository=None)
    container = get_container()
    original_service = container.billing_events_service
    container.billing_events_service = service
    try:
        yield service
    finally:
        container.billing_events_service = original_service


def _signature(payload: str, secret: str) -> str:
    timestamp = int(time.time())
    signed = f"{timestamp}.{payload}".encode()
    import hashlib
    import hmac

    digest = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "stripe"


def load_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fixture_name, tenant_id",
    [
        ("customer.subscription.created.json", "11111111-2222-3333-4444-555555555555"),
        ("invoice.payment_failed.json", "11111111-2222-3333-4444-555555555555"),
    ],
)
async def test_webhook_replays_fixture(
    fixture_name: str,
    tenant_id: str,
    webhook_app: FastAPI,
    sqlite_stripe_repo: StripeEventRepository,
    fake_billing_events: BillingEventsService,
):
    body = load_fixture(fixture_name)
    payload = json.loads(body)

    headers = {
        "stripe-signature": _signature(body, "whsec_test"),
        "content-type": "application/json",
    }

    transport = ASGITransport(app=webhook_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.post("/webhooks/stripe", content=body, headers=headers)

    assert resp.status_code == 202
    stored = await sqlite_stripe_repo.get_by_event_id(payload["id"])
    assert stored is not None
    assert stored.processing_outcome == StripeEventStatus.PROCESSED.value
    assert stored.processed_at is not None
    assert stored.tenant_hint == tenant_id

    stream = await fake_billing_events.subscribe(tenant_id)
    message = await stream.next_message(timeout=0.2)
    await stream.close()
    assert message is not None
    data = json.loads(message)
    assert data["event_type"] == payload["type"]
    if payload["type"].startswith("customer.subscription"):
        assert data["subscription"]["status"] == payload["data"]["object"].get("status")
    if payload["type"].startswith("invoice."):
        assert data["invoice"]["status"] == payload["data"]["object"].get("status")


@pytest.mark.asyncio
async def test_duplicate_event_is_acknowledged(
    webhook_app: FastAPI,
    sqlite_stripe_repo: StripeEventRepository,
    fake_billing_events: BillingEventsService,
):
    body = load_fixture("invoice.payment_failed.json")
    headers = {
        "stripe-signature": _signature(body, "whsec_test"),
        "content-type": "application/json",
    }

    transport = ASGITransport(app=webhook_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        first = await client.post("/webhooks/stripe", content=body, headers=headers)
        second = await client.post("/webhooks/stripe", content=body, headers=headers)

    assert first.status_code == 202
    assert second.status_code == 202
    assert second.json()["duplicate"] is True
    payload = json.loads(body)
    stored = await sqlite_stripe_repo.get_by_event_id(payload["id"])
    assert stored is not None
    assert stored.processing_attempts >= 1


@pytest.mark.asyncio
async def test_invalid_signature_returns_400(
    webhook_app: FastAPI, sqlite_stripe_repo: StripeEventRepository
):
    body = json.dumps({"id": "evt_bad", "type": "invoice.payment_failed"})
    transport = ASGITransport(app=webhook_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.post(
            "/webhooks/stripe",
            content=body,
            headers={"stripe-signature": "t=0,v1=bad", "content-type": "application/json"},
        )

    assert resp.status_code == 400
    assert await sqlite_stripe_repo.get_by_event_id("evt_bad") is None
