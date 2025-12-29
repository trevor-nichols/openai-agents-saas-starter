"""Stripe-specific billing helpers (gateway, dispatchers, workers, event schemas)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .event_models import (
    DispatchBroadcastContext,
    DispatchResult,
    InvoiceSnapshotView,
    SubscriptionSnapshotView,
    UsageDelta,
)
from .gateway import StripeGateway, get_stripe_gateway

if TYPE_CHECKING:  # pragma: no cover - typing-only imports
    from .dispatcher import (
        StripeEventDispatcher,
        get_stripe_event_dispatcher,
        stripe_event_dispatcher,
    )
    from .retry_worker import StripeDispatchRetryWorker

__all__ = [
    "DispatchBroadcastContext",
    "DispatchResult",
    "InvoiceSnapshotView",
    "StripeDispatchRetryWorker",
    "StripeEventDispatcher",
    "StripeGateway",
    "SubscriptionSnapshotView",
    "UsageDelta",
    "get_stripe_gateway",
    "get_stripe_event_dispatcher",
    "stripe_event_dispatcher",
]


def __getattr__(name: str):
    if name in {"StripeEventDispatcher", "get_stripe_event_dispatcher", "stripe_event_dispatcher"}:
        from . import dispatcher as _dispatcher

        return getattr(_dispatcher, name)
    if name == "StripeDispatchRetryWorker":
        from . import retry_worker as _retry_worker

        return _retry_worker.StripeDispatchRetryWorker
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(__all__)
