"""Integration tests for the Stripe replay CLI helpers."""

from __future__ import annotations

import importlib.util
from collections.abc import AsyncIterator
from importlib.abc import Loader
from pathlib import Path
from typing import Any, cast

import pytest
from sqlalchemy import Table
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.persistence.stripe.models import (
    StripeDispatchStatus,
    StripeEvent,
    StripeEventDispatch,
)
from app.infrastructure.persistence.stripe.repository import StripeEventRepository
from app.services.billing_service import BillingService
from app.services.stripe_dispatcher import stripe_event_dispatcher
from tests.utils.sqlalchemy import create_tables

_REPLAY_MODULE = Path(__file__).resolve().parents[3] / "scripts" / "stripe" / "replay_events.py"
_SPEC = importlib.util.spec_from_file_location("replay_events", _REPLAY_MODULE)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("stripe replay module could not be loaded")
replay_events = importlib.util.module_from_spec(_SPEC)
loader = cast(Loader, _SPEC.loader)
loader.exec_module(replay_events)

pytestmark = pytest.mark.stripe_replay


class _FakeBillingService:
    def __init__(self) -> None:
        self.subscription_calls: int = 0

    async def sync_subscription_from_processor(self, *_args, **_kwargs) -> None:
        self.subscription_calls += 1


STRIPE_TABLES = cast(
    tuple[Table, ...],
    (
        StripeEvent.__table__,
        StripeEventDispatch.__table__,
    ),
)


@pytest.fixture
async def sqlite_repo() -> AsyncIterator[tuple[StripeEventRepository, _FakeBillingService]]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(lambda connection: create_tables(connection, STRIPE_TABLES))
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    repo = StripeEventRepository(session_factory)
    fake_billing = _FakeBillingService()
    stripe_event_dispatcher.configure(
        repository=repo,
        billing=cast(BillingService, fake_billing),
    )
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


def _subscription_payload() -> dict[str, Any]:
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
