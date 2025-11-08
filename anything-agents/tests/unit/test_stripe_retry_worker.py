"""Unit tests for the Stripe dispatch retry worker."""

from __future__ import annotations

import asyncio
import uuid
from types import SimpleNamespace

import pytest

from app.observability.metrics import STRIPE_DISPATCH_RETRY_TOTAL
from app.services.stripe_retry_worker import StripeDispatchRetryWorker


class _FakeRepository:
    def __init__(self, dispatch_count: int = 1) -> None:
        self._dispatches = [
            SimpleNamespace(id=uuid.uuid4(), handler="billing_sync") for _ in range(dispatch_count)
        ]

    async def list_dispatches_for_retry(self, *, limit: int, ready_before):
        if not self._dispatches:
            await asyncio.sleep(0)
            return []
        batch, self._dispatches = self._dispatches[:limit], self._dispatches[limit:]
        return batch


class _FakeDispatcher:
    def __init__(self, fail_first: bool = False) -> None:
        self.fail_first = fail_first
        self.calls: list[uuid.UUID] = []

    async def replay_dispatch(self, dispatch_id: uuid.UUID) -> None:
        self.calls.append(dispatch_id)
        if self.fail_first:
            self.fail_first = False
            raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_worker_replays_due_dispatches():
    repo = _FakeRepository(dispatch_count=1)
    dispatcher = _FakeDispatcher()
    worker = StripeDispatchRetryWorker(poll_interval_seconds=0.05, batch_size=5)
    worker.configure(repository=repo, dispatcher=dispatcher)

    before = _counter_value(result="success")

    await worker.start()
    await asyncio.sleep(0.2)
    await worker.shutdown()

    assert dispatcher.calls, "Expected the worker to replay the pending dispatch"
    after = _counter_value(result="success")
    assert after >= before + 1


@pytest.mark.asyncio
async def test_worker_continues_after_dispatch_failure():
    repo = _FakeRepository(dispatch_count=2)
    dispatcher = _FakeDispatcher(fail_first=True)
    worker = StripeDispatchRetryWorker(poll_interval_seconds=0.05, batch_size=1)
    worker.configure(repository=repo, dispatcher=dispatcher)

    before_fail = _counter_value(result="failed")
    before_success = _counter_value(result="success")

    await worker.start()
    await asyncio.sleep(0.3)
    await worker.shutdown()

    assert len(dispatcher.calls) >= 2
    assert _counter_value(result="failed") >= before_fail + 1
    assert _counter_value(result="success") >= before_success + 1


def _counter_value(*, result: str) -> float:
    return STRIPE_DISPATCH_RETRY_TOTAL.labels(handler="billing_sync", result=result)._value.get()
