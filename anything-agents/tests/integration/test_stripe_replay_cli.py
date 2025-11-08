"""Integration tests for the Stripe replay CLI helpers."""

from __future__ import annotations

import asyncio

import pytest
from pathlib import Path
import importlib.util

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.persistence.stripe.models import (
    StripeDispatchStatus,
    StripeEvent,
    StripeEventDispatch,
)
from app.infrastructure.persistence.stripe.repository import StripeEventRepository
from app.services.stripe_dispatcher import stripe_event_dispatcher

_REPLAY_MODULE = Path(__file__).resolve().parents[3] / "scripts" / "stripe" / "replay_events.py"
_SPEC = importlib.util.spec_from_file_location("replay_events", _REPLAY_MODULE)
assert _SPEC and _SPEC.loader
replay_events = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(replay_events)  # type: ignore[arg-type]

pytestmark = pytest.mark.stripe_replay


class _FakeBillingService:
    def __init__(self) -> None:
        self.subscription_calls: int = 0

    async def sync_subscription_from_processor(self, *_args, **_kwargs) -> None:
        self.subscription_calls += 1


@pytest.fixture
async def sqlite_repo():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(StripeEvent.__table__.create)
        await conn.run_sync(StripeEventDispatch.__table__.create)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    repo = StripeEventRepository(session_factory)
    fake_billing = _FakeBillingService()
    stripe_event_dispatcher.configure(repository=repo, billing=fake_billing)  # type: ignore[arg-type]
    try:
        yield repo, fake_billing
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_cli_replay_completes_failed_dispatch(sqlite_repo, capsys):
    repo, fake_billing = sqlite_repo
    payload = _subscription_payload()
    event, _ = await repo.upsert_event(
        stripe_event_id=payload["id"],
        event_type=payload["type"],
        payload=payload,
        tenant_hint="tenant-cli",
        stripe_created_at=None,
    )
    dispatch = await repo.ensure_dispatch(event_id=event.id, handler="billing_sync")
    await repo.mark_dispatch_failed(dispatch.id, error="boom")

    await replay_events.cmd_replay(
        repo,
        dispatch_ids=[str(dispatch.id)],
        event_ids=None,
        status=None,
        limit=1,
        handler="billing_sync",
        assume_yes=True,
    )

    refreshed = await repo.get_dispatch(dispatch.id)
    assert refreshed is not None
    assert refreshed.status == StripeDispatchStatus.COMPLETED.value
    assert fake_billing.subscription_calls == 1
    captured = capsys.readouterr()
    assert "Replayed dispatch" in captured.out


def _subscription_payload() -> dict:
    return {
        "id": "evt_cli",
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "id": "sub_cli",
                "status": "active",
                "metadata": {
                    "tenant_id": "tenant-cli",
                    "plan_code": "starter",
                },
                "items": {
                    "data": [
                        {
                            "price": {
                                "id": "price_123",
                                "metadata": {"plan_code": "starter"},
                                "nickname": "starter",
                            },
                            "quantity": 1,
                        }
                    ]
                },
            }
        },
    }
