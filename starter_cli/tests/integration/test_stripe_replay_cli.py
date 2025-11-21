"""Integration tests for the Stripe replay CLI helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, cast

import pytest
from sqlalchemy import Table
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from starter_cli.commands.stripe import replay_dispatches_with_repo

import app.infrastructure.persistence.tenants.models  # noqa: F401  # register tenant models for SA relationships
from app.infrastructure.persistence.stripe.models import (
    StripeDispatchStatus,
    StripeEvent,
    StripeEventDispatch,
)
from app.infrastructure.persistence.stripe.repository import StripeEventRepository
from app.services.billing.billing_service import BillingService
from app.services.billing.stripe.dispatcher import StripeEventDispatcher
from tests.utils.sqlalchemy import create_tables

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
    yield repo, fake_billing
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

    dispatcher = StripeEventDispatcher()
    dispatcher.configure(repository=repo, billing=cast(BillingService, fake_billing))

    await replay_dispatches_with_repo(
        repo,
        dispatch_ids=[str(dispatch.id)],
        event_ids=None,
        status=None,
        limit=1,
        handler="billing_sync",
        assume_yes=True,
        dispatcher=dispatcher,
        billing=cast(BillingService, fake_billing),
        confirm=lambda _targets: True,
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
