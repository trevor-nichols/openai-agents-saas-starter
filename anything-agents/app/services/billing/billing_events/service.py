"""Billing events service orchestrating publisher + history readers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.infrastructure.persistence.stripe.models import StripeEvent, StripeEventStatus
from app.infrastructure.persistence.stripe.repository import StripeEventRepository
from app.services.billing.stripe.event_models import DispatchBroadcastContext

from .history import BillingEventHistoryPage, BillingEventHistoryReader
from .normalizer import BillingEventNormalizer
from .payloads import (
    BillingEventInvoice,
    BillingEventPayload,
    BillingEventSubscription,
    BillingEventUsage,
)
from .protocols import BillingEventBackend, BillingEventStream
from .publisher import BillingEventPublisher
from .types import JSONDict


class BillingEventsService:
    """Coordinates billing event publishing and historical reads."""

    def __init__(self, normalizer: BillingEventNormalizer | None = None) -> None:
        self._normalizer = normalizer or BillingEventNormalizer()
        self._publisher = BillingEventPublisher(normalizer=self._normalizer)
        self._history_reader = BillingEventHistoryReader(normalizer=self._normalizer)

    def configure(
        self,
        *,
        backend: BillingEventBackend | None = None,
        repository: StripeEventRepository | None = None,
    ) -> None:
        self._publisher.configure(backend=backend, repository=repository)
        self._history_reader.configure(repository)

    async def shutdown(self) -> None:
        await self._publisher.shutdown()

    async def startup(self) -> None:
        await self._publisher.startup()

    async def publish_from_event(
        self,
        record: StripeEvent,
        payload: JSONDict,
        context: DispatchBroadcastContext | None = None,
    ) -> None:
        await self._publisher.publish_from_event(record, payload, context)

    async def mark_processed(self, processed_at: datetime | None) -> None:
        await self._publisher.mark_processed(processed_at)

    async def subscribe(self, tenant_id: str) -> BillingEventStream:
        return await self._publisher.subscribe(tenant_id)

    async def publish_raw(self, tenant_id: str, message: JSONDict) -> None:
        await self._publisher.publish_raw(tenant_id, message)

    async def list_history(
        self,
        *,
        tenant_id: str,
        limit: int = 25,
        cursor: str | None = None,
        event_type: str | None = None,
        status: StripeEventStatus | str | None = None,
    ) -> BillingEventHistoryPage:
        return await self._history_reader.list_history(
            tenant_id=tenant_id,
            limit=limit,
            cursor=cursor,
            event_type=event_type,
            status=status,
        )


def get_billing_events_service() -> BillingEventsService:
    """Resolve the container-backed billing events service."""

    from app.bootstrap.container import get_container

    return get_container().billing_events_service


@dataclass(slots=True)
class _BillingEventsServiceHandle:
    """Proxy exposing the configured billing events service."""

    def __getattr__(self, name: str):  # pragma: no cover - passthrough logic
        return getattr(get_billing_events_service(), name)


billing_events_service = _BillingEventsServiceHandle()


__all__ = [
    "BillingEventBackend",
    "BillingEventHistoryPage",
    "BillingEventInvoice",
    "BillingEventPayload",
    "BillingEventsService",
    "BillingEventStream",
    "BillingEventSubscription",
    "BillingEventUsage",
    "billing_events_service",
    "get_billing_events_service",
]
