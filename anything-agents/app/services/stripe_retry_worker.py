"""Background worker for retrying failed Stripe dispatches."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from app.infrastructure.persistence.stripe.models import StripeEventDispatch
from app.observability.metrics import observe_dispatch_retry
from app.services.stripe_dispatcher import get_stripe_event_dispatcher
from app.services.stripe_event_models import DispatchResult

logger = logging.getLogger("anything-agents.services.stripe_retry_worker")


class StripeDispatchRepository(Protocol):
    async def list_dispatches_for_retry(
        self,
        *,
        limit: int,
        ready_before: datetime,
    ) -> list[StripeEventDispatch]:
        """Return dispatch rows that should be retried."""
        ...


class StripeDispatchExecutor(Protocol):
    async def replay_dispatch(self, dispatch_id: UUID) -> DispatchResult:  # pragma: no cover
        """Attempt to replay a single dispatch identified by its primary key."""
        ...


class StripeDispatchRetryWorker:
    """Periodically replays failed Stripe dispatch rows."""

    def __init__(
        self,
        *,
        poll_interval_seconds: float = 30.0,
        batch_size: int = 10,
    ) -> None:
        self._repository: StripeDispatchRepository | None = None
        self._dispatcher: StripeDispatchExecutor | None = None
        self._poll_interval_seconds = poll_interval_seconds
        self._batch_size = batch_size
        self._task: asyncio.Task[None] | None = None
        self._stop_event: asyncio.Event | None = None

    def configure(
        self,
        *,
        repository: StripeDispatchRepository,
        dispatcher: StripeDispatchExecutor | None = None,
    ) -> None:
        self._repository = repository
        self._dispatcher = dispatcher or get_stripe_event_dispatcher()

    async def start(self) -> None:
        if self._task is not None:
            return
        if self._repository is None or self._dispatcher is None:
            raise RuntimeError("StripeDispatchRetryWorker not configured.")
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self._run(), name="stripe-dispatch-retry")

    async def shutdown(self) -> None:
        if self._task is None:
            return
        stop_event = self._require_stop_event()
        stop_event.set()
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:  # pragma: no cover - normal shutdown path
            pass
        finally:
            self._task = None
            self._stop_event = None

    async def _run(self) -> None:
        stop_event = self._require_stop_event()
        while not stop_event.is_set():
            await self._process_due_dispatches()
            try:
                await asyncio.wait_for(
                    stop_event.wait(),
                    timeout=self._poll_interval_seconds,
                )
            except TimeoutError:
                continue

    async def _process_due_dispatches(self) -> None:
        repository = self._require_repository()
        dispatcher = self._require_dispatcher()
        try:
            due_dispatches = await repository.list_dispatches_for_retry(
                limit=self._batch_size,
                ready_before=datetime.now(UTC),
            )
        except Exception:  # pragma: no cover - defensive logging
            logger.exception("Failed to enumerate Stripe dispatches for retry")
            return

        if not due_dispatches:
            return

        stop_event = self._require_stop_event()
        for dispatch in due_dispatches:
            if stop_event.is_set():
                return
            await self._replay(dispatcher, dispatch)

    async def _replay(
        self,
        dispatcher: StripeDispatchExecutor,
        dispatch: StripeEventDispatch,
    ) -> None:
        try:
            await dispatcher.replay_dispatch(dispatch.id)
            observe_dispatch_retry(handler=dispatch.handler, result="success")
            logger.info(
                "Retried Stripe dispatch",
                extra={"dispatch_id": str(dispatch.id), "handler": dispatch.handler},
            )
        except Exception:  # pragma: no cover - dispatcher handles bookkeeping
            observe_dispatch_retry(handler=dispatch.handler, result="failed")
            logger.exception(
                "Automatic replay failed",
                extra={"dispatch_id": str(dispatch.id), "handler": dispatch.handler},
            )

    def _require_repository(self) -> StripeDispatchRepository:
        if self._repository is None:
            raise RuntimeError("StripeDispatchRetryWorker repository not configured")
        return self._repository

    def _require_dispatcher(self) -> StripeDispatchExecutor:
        if self._dispatcher is None:
            raise RuntimeError("StripeDispatchRetryWorker dispatcher not configured")
        return self._dispatcher

    def _require_stop_event(self) -> asyncio.Event:
        if self._stop_event is None:
            raise RuntimeError("StripeDispatchRetryWorker not started")
        return self._stop_event


def get_stripe_dispatch_retry_worker() -> StripeDispatchRetryWorker:
    """Resolve the configured Stripe dispatch retry worker."""

    from app.bootstrap.container import get_container

    return get_container().stripe_dispatch_retry_worker


class _StripeDispatchRetryWorkerHandle:
    """Proxy exposing the container-backed retry worker."""

    def __getattr__(self, name: str):
        return getattr(get_stripe_dispatch_retry_worker(), name)


stripe_dispatch_retry_worker = _StripeDispatchRetryWorkerHandle()

__all__ = [
    "StripeDispatchRetryWorker",
    "get_stripe_dispatch_retry_worker",
    "stripe_dispatch_retry_worker",
]
