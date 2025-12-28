"""Stripe webhook dispatch orchestration service."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from app.infrastructure.persistence.stripe.models import (
    StripeEvent,
    StripeEventDispatch,
    StripeEventStatus,
)
from app.infrastructure.persistence.stripe.repository import StripeEventRepository
from app.observability.logging import log_context, log_event
from app.services.billing.billing_service import (
    BillingService,
    ProcessorInvoiceLineSnapshot,
    ProcessorInvoiceSnapshot,
    ProcessorSubscriptionSnapshot,
)
from app.services.billing.stripe.event_models import (
    DispatchBroadcastContext,
    DispatchResult,
    InvoiceSnapshotView,
    SubscriptionSnapshotView,
    UsageDelta,
)

JSONDict = dict[str, Any]
HandlerFunc = Callable[[StripeEvent, JSONDict], Awaitable[DispatchBroadcastContext | None]]


@dataclass(slots=True)
class EventHandler:
    name: str
    func: HandlerFunc


class StripeEventDispatcher:
    """Routes stored Stripe events through domain handlers."""

    def __init__(self) -> None:
        self._repository: StripeEventRepository | None = None
        self._billing_service: BillingService | None = None
        self._handlers: dict[str, EventHandler] = {}
        self._retry_base_seconds = 30.0
        self._retry_max_seconds = 10 * 60.0

    def configure(
        self,
        *,
        repository: StripeEventRepository,
        billing: BillingService,
    ) -> None:
        self._repository = repository
        self._billing_service = billing
        self._handlers = self._build_handlers()

    def _build_handlers(self) -> dict[str, EventHandler]:
        return {
            "customer.subscription.created": EventHandler(
                "billing_sync", self._handle_subscription_event
            ),
            "customer.subscription.updated": EventHandler(
                "billing_sync", self._handle_subscription_event
            ),
            "customer.subscription.deleted": EventHandler(
                "billing_sync", self._handle_subscription_event
            ),
            "invoice.payment_succeeded": EventHandler("invoice_sync", self._handle_invoice_event),
            "invoice.payment_failed": EventHandler("invoice_sync", self._handle_invoice_event),
            "invoice.paid": EventHandler("invoice_sync", self._handle_invoice_event),
            "invoice.finalized": EventHandler("invoice_sync", self._handle_invoice_event),
            "invoice.payment_action_required": EventHandler(
                "invoice_sync", self._handle_invoice_event
            ),
        }

    async def dispatch_now(self, event: StripeEvent, payload: JSONDict) -> DispatchResult:
        with log_context(worker_id="stripe-dispatcher", stripe_event_id=event.stripe_event_id):
            handler = self._handlers.get(event.event_type)
            repository = self._require_repository()
            if handler is None:
                processed_at = await repository.record_outcome(
                    event.id, status=StripeEventStatus.PROCESSED
                )
                log_event(
                    "stripe.dispatch.no_handler",
                    level="debug",
                    event_type=event.event_type,
                    stripe_event_id=event.stripe_event_id,
                )
                return DispatchResult(processed_at=processed_at)

            dispatch = await repository.ensure_dispatch(event_id=event.id, handler=handler.name)
            return await self._execute_handler(dispatch, event, payload, handler)

    async def replay_dispatch(self, dispatch_id: uuid.UUID) -> DispatchResult:
        with log_context(worker_id="stripe-dispatcher", stripe_dispatch_id=str(dispatch_id)):
            repository = self._require_repository()
            dispatch = await repository.get_dispatch(dispatch_id)
            if dispatch is None:
                raise ValueError(f"Dispatch {dispatch_id} not found")
            event = await repository.get_event_by_uuid(dispatch.stripe_event_id)
            if event is None:
                raise ValueError("Parent Stripe event missing for dispatch replay")
            handler = self._handlers.get(event.event_type)
            if handler is None:
                await repository.mark_dispatch_completed(dispatch.id)
                processed_at = await repository.record_outcome(
                    event.id, status=StripeEventStatus.PROCESSED
                )
                return DispatchResult(processed_at=processed_at)
            await repository.reset_dispatch(dispatch.id)
            return await self._execute_handler(dispatch, event, event.payload, handler)

    async def _execute_handler(
        self,
        dispatch: StripeEventDispatch,
        event: StripeEvent,
        payload: JSONDict,
        handler: EventHandler,
    ) -> DispatchResult:
        repository = self._require_repository()
        refreshed_dispatch = await repository.mark_dispatch_in_progress(dispatch.id)
        if refreshed_dispatch is None:
            raise RuntimeError("Stripe dispatch row missing when starting handler")
        dispatch = refreshed_dispatch
        try:
            context = await handler.func(event, payload)
        except Exception as exc:  # pragma: no cover - re-raised after bookkeeping
            error_message = str(exc)
            retry_at = self._next_retry_time(dispatch.attempts)
            await repository.mark_dispatch_failed(
                dispatch.id,
                error=error_message,
                next_retry_at=retry_at,
            )
            await repository.record_outcome(
                event.id,
                status=StripeEventStatus.FAILED,
                error=error_message,
            )
            log_event(
                "stripe.dispatch.failed",
                level="error",
                handler=handler.name,
                stripe_event_id=event.stripe_event_id,
                attempts=dispatch.attempts,
                next_retry_at=retry_at,
                exc_info=exc,
            )
            raise
        else:
            await repository.mark_dispatch_completed(dispatch.id)
            processed_at = await repository.record_outcome(
                event.id,
                status=StripeEventStatus.PROCESSED,
            )
            log_event(
                "stripe.dispatch.completed",
                handler=handler.name,
                stripe_event_id=event.stripe_event_id,
                attempts=dispatch.attempts,
            )
            return DispatchResult(processed_at=processed_at, broadcast=context)

    async def _handle_subscription_event(
        self, event: StripeEvent, payload: JSONDict
    ) -> DispatchBroadcastContext:
        billing = self._require_billing_service()
        snapshot = self._build_subscription_snapshot(payload)
        await billing.sync_subscription_from_processor(snapshot)
        return DispatchBroadcastContext(
            tenant_id=snapshot.tenant_id,
            event_type=event.event_type,
            summary=f"Subscription {snapshot.status}",
            status=snapshot.status,
            subscription=self._subscription_view(snapshot),
        )

    async def _handle_invoice_event(
        self, event: StripeEvent, payload: JSONDict
    ) -> DispatchBroadcastContext:
        billing = self._require_billing_service()
        snapshot = self._build_invoice_snapshot(event, payload)
        await billing.ingest_invoice_snapshot(snapshot)
        summary = snapshot.description or snapshot.billing_reason or f"Invoice {snapshot.status}"
        usage = [
            self._usage_delta_from_line(line)
            for line in snapshot.lines
            if line.quantity not in (None, 0)
        ]
        return DispatchBroadcastContext(
            tenant_id=snapshot.tenant_id,
            event_type=event.event_type,
            summary=summary,
            status=snapshot.status,
            invoice=self._invoice_view(snapshot),
            usage=usage,
        )

    def _build_subscription_snapshot(self, payload: JSONDict) -> ProcessorSubscriptionSnapshot:
        data_obj = (payload.get("data") or {}).get("object") or {}
        metadata = _normalize_metadata(data_obj.get("metadata") or {})
        tenant_id = metadata.get("tenant_id") or metadata.get("tenant")
        if not tenant_id:
            raise ValueError("Missing tenant_id in subscription metadata")
        plan_code = (
            metadata.get("plan_code")
            or metadata.get("plan")
            or self._extract_plan_code_from_items(data_obj)
        )
        if not plan_code:
            raise ValueError("Unable to determine plan_code from subscription event")
        customer_id = data_obj.get("customer") or metadata.get("customer_id")
        price_id = self._extract_price_id(data_obj)
        seat_count = self._extract_quantity(data_obj)
        schedule_id = _extract_schedule_id(data_obj.get("schedule"))
        if schedule_id is not None:
            metadata["processor_schedule_id"] = schedule_id
        else:
            metadata["processor_schedule_id"] = ""
        snapshot = ProcessorSubscriptionSnapshot(
            tenant_id=str(tenant_id),
            plan_code=str(plan_code),
            status=str(data_obj.get("status", "unknown")),
            auto_renew=not bool(data_obj.get("cancel_at_period_end")),
            starts_at=_coerce_datetime(
                data_obj.get("start_date") or data_obj.get("current_period_start")
            ),
            current_period_start=_coerce_datetime(data_obj.get("current_period_start")),
            current_period_end=_coerce_datetime(data_obj.get("current_period_end")),
            trial_ends_at=_coerce_datetime(data_obj.get("trial_end")),
            cancel_at=_coerce_datetime(data_obj.get("cancel_at")),
            seat_count=seat_count,
            billing_email=data_obj.get("customer_email") or metadata.get("billing_email"),
            processor_customer_id=customer_id,
            processor_subscription_id=str(data_obj.get("id")),
            metadata={
                **metadata,
                "processor_price_id": price_id or "",
                "processor_status": str(data_obj.get("status")),
            },
        )
        return snapshot

    def _subscription_view(
        self, snapshot: ProcessorSubscriptionSnapshot
    ) -> SubscriptionSnapshotView:
        return SubscriptionSnapshotView(
            tenant_id=snapshot.tenant_id,
            plan_code=snapshot.plan_code,
            status=snapshot.status,
            auto_renew=snapshot.auto_renew,
            seat_count=snapshot.seat_count,
            current_period_start=snapshot.current_period_start,
            current_period_end=snapshot.current_period_end,
            trial_ends_at=snapshot.trial_ends_at,
            cancel_at=snapshot.cancel_at,
        )

    def _build_invoice_snapshot(
        self, event: StripeEvent, payload: JSONDict
    ) -> ProcessorInvoiceSnapshot:
        stripe_data = cast(JSONDict, payload.get("data") or {})
        data_obj = cast(JSONDict, stripe_data.get("object") or {})
        metadata = cast(JSONDict, data_obj.get("metadata") or {})
        tenant_id = metadata.get("tenant_id") or metadata.get("tenant") or event.tenant_hint
        if not tenant_id:
            raise ValueError("Missing tenant_id in invoice metadata")

        lines = self._build_invoice_lines(data_obj)
        period_start = _coerce_datetime(data_obj.get("period_start"))
        period_end = _coerce_datetime(data_obj.get("period_end"))
        if period_start is None and lines:
            period_start = lines[0].period_start
        if period_end is None and lines:
            period_end = lines[0].period_end

        snapshot = ProcessorInvoiceSnapshot(
            tenant_id=str(tenant_id),
            invoice_id=str(data_obj.get("id")),
            status=str(data_obj.get("status", "unknown")),
            amount_due_cents=int(data_obj.get("amount_due") or data_obj.get("total") or 0),
            currency=str(data_obj.get("currency") or "usd"),
            period_start=period_start,
            period_end=period_end,
            hosted_invoice_url=data_obj.get("hosted_invoice_url") or data_obj.get("invoice_pdf"),
            billing_reason=data_obj.get("billing_reason"),
            collection_method=data_obj.get("collection_method"),
            description=data_obj.get("description"),
            lines=lines,
        )
        return snapshot

    def _invoice_view(self, snapshot: ProcessorInvoiceSnapshot) -> InvoiceSnapshotView:
        return InvoiceSnapshotView(
            tenant_id=snapshot.tenant_id,
            invoice_id=snapshot.invoice_id,
            status=snapshot.status,
            amount_due_cents=snapshot.amount_due_cents,
            currency=snapshot.currency,
            billing_reason=snapshot.billing_reason,
            hosted_invoice_url=snapshot.hosted_invoice_url,
            collection_method=snapshot.collection_method,
            period_start=snapshot.period_start,
            period_end=snapshot.period_end,
        )

    def _usage_delta_from_line(self, line: ProcessorInvoiceLineSnapshot) -> UsageDelta:
        return UsageDelta(
            feature_key=line.feature_key,
            quantity=line.quantity or 0,
            period_start=line.period_start,
            period_end=line.period_end,
            idempotency_key=line.idempotency_key,
            amount_cents=line.amount_cents,
        )

    def _build_invoice_lines(self, invoice_obj: JSONDict) -> list[ProcessorInvoiceLineSnapshot]:
        items = ((invoice_obj.get("lines") or {}).get("data")) or []
        lines: list[ProcessorInvoiceLineSnapshot] = []
        for line in items:
            price = cast(JSONDict, line.get("price") or {})
            recurring = cast(JSONDict, price.get("recurring") or {})
            usage_type = recurring.get("usage_type")
            is_metered = usage_type == "metered" or bool(line.get("usage_record_summary"))
            if not is_metered:
                continue
            metadata = cast(JSONDict, (line.get("metadata") or {}))
            price_metadata = cast(JSONDict, price.get("metadata") or {})
            metadata = metadata | price_metadata
            feature_key = metadata.get("feature_key") or metadata.get("plan_feature")
            if not feature_key:
                feature_key = price.get("nickname") or line.get("description")
            quantity = line.get("quantity")
            if not feature_key or quantity in (None, 0):
                continue
            period = line.get("period") or {}
            lines.append(
                ProcessorInvoiceLineSnapshot(
                    feature_key=str(feature_key),
                    quantity=int(quantity),
                    period_start=_coerce_datetime(period.get("start")),
                    period_end=_coerce_datetime(period.get("end")),
                    idempotency_key=line.get("id"),
                    amount_cents=int(line.get("amount") or 0),
                )
            )
        return lines

    def _extract_plan_code_from_items(self, data_obj: JSONDict) -> str | None:
        items = ((data_obj.get("items") or {}).get("data")) or []
        if not items:
            return None
        price = items[0].get("price") or {}
        price_metadata = price.get("metadata") or {}
        return (
            price_metadata.get("plan_code")
            or price_metadata.get("starter_console_plan_code")
            or price.get("nickname")
        )

    def _extract_price_id(self, data_obj: JSONDict) -> str | None:
        items = ((data_obj.get("items") or {}).get("data")) or []
        if not items:
            return None
        price = items[0].get("price") or {}
        return price.get("id")

    def _extract_quantity(self, data_obj: JSONDict) -> int | None:
        items = ((data_obj.get("items") or {}).get("data")) or []
        if not items:
            return data_obj.get("quantity")
        return items[0].get("quantity")

    def _next_retry_time(self, attempts: int) -> datetime:
        delay = self._retry_base_seconds * (2 ** max(attempts - 1, 0))
        delay = min(delay, self._retry_max_seconds)
        return datetime.now(UTC) + timedelta(seconds=delay)

    def _require_repository(self) -> StripeEventRepository:
        if self._repository is None:
            raise RuntimeError("StripeEventRepository has not been configured for dispatcher")
        return self._repository

    def _require_billing_service(self) -> BillingService:
        if self._billing_service is None:
            raise RuntimeError("BillingService has not been configured for dispatcher")
        return self._billing_service


def _coerce_datetime(value) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    try:
        return datetime.fromtimestamp(float(value), tz=UTC)
    except (TypeError, ValueError):  # pragma: no cover - guard rails for malformed data
        return None


def _normalize_metadata(metadata: dict[str, object]) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for key, value in metadata.items():
        if value is None:
            continue
        cleaned[str(key)] = str(value)
    return cleaned


def _extract_schedule_id(value: object) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        schedule_id = value.get("id")
        return str(schedule_id) if schedule_id else None
    schedule_id = getattr(value, "id", None)
    return str(schedule_id) if schedule_id else None


def get_stripe_event_dispatcher() -> StripeEventDispatcher:
    """Resolve the configured Stripe event dispatcher."""

    from app.bootstrap.container import get_container

    return get_container().stripe_event_dispatcher


class _StripeEventDispatcherHandle:
    """Proxy exposing the container-backed dispatcher."""

    def __getattr__(self, name: str):
        return getattr(get_stripe_event_dispatcher(), name)


stripe_event_dispatcher = _StripeEventDispatcherHandle()

__all__ = [
    "StripeEventDispatcher",
    "get_stripe_event_dispatcher",
    "stripe_event_dispatcher",
]
