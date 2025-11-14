"""Billing event broadcasting and streaming helpers."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import uuid
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

from redis.asyncio import Redis

from app.infrastructure.persistence.stripe.models import StripeEvent, StripeEventStatus
from app.infrastructure.persistence.stripe.repository import StripeEventRepository
from app.observability.metrics import (
    observe_stripe_webhook_event,
    record_billing_stream_backlog,
    record_billing_stream_event,
)
from app.services.stripe_event_models import (
    DispatchBroadcastContext,
    InvoiceSnapshotView,
    SubscriptionSnapshotView,
    UsageDelta,
)

logger = logging.getLogger("anything-agents.services.billing_events")


@dataclass(slots=True)
class BillingEventPayload:
    tenant_id: str
    event_type: str
    stripe_event_id: str
    occurred_at: str
    summary: str | None
    status: str
    subscription: BillingEventSubscription | None = None
    invoice: BillingEventInvoice | None = None
    usage: list[BillingEventUsage] = field(default_factory=list)


@dataclass(slots=True)
class BillingEventSubscription:
    plan_code: str
    status: str
    seat_count: int | None
    auto_renew: bool
    current_period_start: str | None
    current_period_end: str | None
    trial_ends_at: str | None
    cancel_at: str | None


@dataclass(slots=True)
class BillingEventInvoice:
    invoice_id: str
    status: str
    amount_due_cents: int
    currency: str
    billing_reason: str | None
    hosted_invoice_url: str | None
    collection_method: str | None
    period_start: str | None
    period_end: str | None


@dataclass(slots=True)
class BillingEventUsage:
    feature_key: str
    quantity: int
    period_start: str | None
    period_end: str | None
    amount_cents: int | None


@dataclass(slots=True)
class BillingEventHistoryPage:
    items: list[BillingEventPayload]
    next_cursor: str | None


class BillingEventStream(Protocol):
    async def next_message(self, timeout: float | None = None) -> str | None: ...

    async def close(self) -> None: ...


class BillingEventBackend(Protocol):
    async def publish(self, channel: str, message: str) -> None: ...

    async def subscribe(self, channel: str) -> BillingEventStream: ...

    async def store_bookmark(self, key: str, value: str) -> None: ...

    async def load_bookmark(self, key: str) -> str | None: ...

    async def close(self) -> None: ...


class RedisBillingEventStream:
    def __init__(
        self,
        redis: Redis,
        stream_key: str,
        *,
        backlog_batch_size: int = 128,
        default_block_seconds: float = 1.0,
    ) -> None:
        self._redis = redis
        self._stream_key = stream_key
        self._backlog_batch_size = backlog_batch_size
        self._default_block_seconds = default_block_seconds
        self._buffer: deque[str] = deque()
        self._last_id = "0-0"
        self._backlog_exhausted = False
        self._closed = False

    async def next_message(self, timeout: float | None = None) -> str | None:
        if self._closed:
            return None

        if self._buffer:
            return self._buffer.popleft()

        if not self._backlog_exhausted:
            await self._load_backlog_batch()
            if self._buffer:
                return self._buffer.popleft()

        block_ms = self._to_block_milliseconds(timeout)
        entries = await self._read_new_entries(block_ms)
        if not entries:
            return None

        for entry_id, fields in entries:
            payload = self._decode_entry(fields)
            if payload is None:
                continue
            self._last_id = entry_id
            self._buffer.append(payload)

        if self._buffer:
            return self._buffer.popleft()
        return None

    async def _load_backlog_batch(self) -> None:
        if self._backlog_exhausted:
            return
        start = "-" if self._last_id == "0-0" else f"({self._last_id}"
        entries = await self._redis.xrange(
            self._stream_key,
            min=start,
            max="+",
            count=self._backlog_batch_size,
        )
        if not entries:
            self._backlog_exhausted = True
            return
        for entry_id, fields in entries:
            payload = self._decode_entry(fields)
            if payload is None:
                continue
            self._last_id = entry_id
            self._buffer.append(payload)
        if len(entries) < self._backlog_batch_size:
            self._backlog_exhausted = True

    async def _read_new_entries(self, block_ms: int | None) -> list[tuple[str, dict]]:
        streams = await self._redis.xread(
            {self._stream_key: self._last_id},
            count=1,
            block=block_ms,
        )
        if not streams:
            return []
        _, entries = streams[0]
        return entries

    def _decode_entry(self, fields: dict) -> str | None:
        data = fields.get("data") or fields.get(b"data")
        if data is None:
            return None
        if isinstance(data, bytes):
            return data.decode("utf-8")
        return str(data)

    def _to_block_milliseconds(self, timeout: float | None) -> int | None:
        interval = timeout if timeout is not None else self._default_block_seconds
        if interval is None:
            return None
        interval = max(interval, 0.01)
        return int(interval * 1000)

    async def close(self) -> None:
        self._closed = True


class RedisBillingEventBackend:
    def __init__(
        self,
        redis: Redis,
        *,
        stream_max_length: int = 1024,
        stream_ttl_seconds: int = 86400,
        backlog_batch_size: int = 128,
    ) -> None:
        self._redis = redis
        self._stream_max_length = stream_max_length
        self._stream_ttl_seconds = stream_ttl_seconds
        self._backlog_batch_size = backlog_batch_size

    async def publish(self, channel: str, message: str) -> None:
        await self._redis.xadd(
            channel,
            {"data": message},
            maxlen=self._stream_max_length,
            approximate=False,
        )
        if self._stream_ttl_seconds > 0:
            await self._redis.expire(channel, self._stream_ttl_seconds)

    async def subscribe(self, channel: str) -> BillingEventStream:
        return RedisBillingEventStream(
            self._redis,
            channel,
            backlog_batch_size=self._backlog_batch_size,
        )

    async def store_bookmark(self, key: str, value: str) -> None:
        await self._redis.set(key, value)

    async def load_bookmark(self, key: str) -> str | None:
        raw = await self._redis.get(key)
        if raw is None:
            return None
        if isinstance(raw, bytes):
            return raw.decode("utf-8")
        return str(raw)

    async def close(self) -> None:
        await self._redis.close()


class BillingEventsService:
    def __init__(self) -> None:
        self._backend: BillingEventBackend | None = None
        self._repository: StripeEventRepository | None = None
        self._channel_prefix = "billing:events:tenant:"
        self._bookmark_key = "billing:events:last_processed_at"
        self._lock = asyncio.Lock()
        self._enabled = False
        self._publish_retry_attempts = 3
        self._publish_retry_delay_seconds = 0.25

    def configure(
        self,
        *,
        backend: BillingEventBackend | None = None,
        repository: StripeEventRepository | None = None,
    ) -> None:
        if backend is not None:
            self._backend = backend
            self._enabled = True
        if repository is not None:
            self._repository = repository

    async def shutdown(self) -> None:
        if self._backend:
            await self._backend.close()
        self._enabled = False

    async def startup(self) -> None:
        if not self._enabled or not self._backend:
            return
        raw = await self._backend.load_bookmark(self._bookmark_key)
        processed_after = None
        if raw:
            try:
                processed_after = datetime.fromisoformat(raw)
            except ValueError:
                logger.warning("Invalid billing events bookmark '%s'; replaying from scratch", raw)
        await self._replay(processed_after)

    async def _replay(self, processed_after: datetime | None) -> None:
        if not self._repository or not self._backend:
            return
        replay_after = processed_after
        while True:
            events = await self._repository.list_processed_events_since(
                processed_after=replay_after,
                limit=500,
            )
            if not events:
                break
            for event in events:
                await self._publish_from_record(event)
                replay_after = event.processed_at or datetime.now(UTC)
            if replay_after is not None:
                await self.mark_processed(replay_after)

    async def publish_from_event(
        self,
        record: StripeEvent,
        payload: dict,
        context: DispatchBroadcastContext | None = None,
    ) -> None:
        if not self._enabled or not self._backend:
            return
        tenant_id = context.tenant_id if context and context.tenant_id else record.tenant_hint
        if not tenant_id:
            logger.debug("Skipping Stripe event %s without tenant hint", record.stripe_event_id)
            record_billing_stream_event(source="webhook", result="skipped_no_tenant")
            return
        await self._publish(record, payload, context, source="webhook")

    async def _publish_from_record(self, record: StripeEvent) -> None:
        await self._publish(record, record.payload, None, source="replay")
        await self.mark_processed(record.processed_at)

    async def _publish(
        self,
        record: StripeEvent,
        payload: dict,
        context: DispatchBroadcastContext | None,
        *,
        source: str,
    ) -> None:
        if not self._backend:
            record_billing_stream_event(source=source, result="skipped_backend")
            return
        message = self._normalize_payload(record, payload, context)
        if message is None:
            record_billing_stream_event(source=source, result="normalization_failed")
            return
        channel = self._channel(message.tenant_id)
        attempts = 0
        while True:
            try:
                await self._backend.publish(channel, json.dumps(asdict(message)))
                break
            except Exception as exc:
                attempts += 1
                logger.warning(
                    "Failed to publish billing event (attempt %s/%s): %s",
                    attempts,
                    self._publish_retry_attempts,
                    exc,
                    extra={
                        "tenant_id": message.tenant_id,
                        "event_type": message.event_type,
                    },
                )
                observe_stripe_webhook_event(
                    event_type=message.event_type, result="broadcast_failed"
                )
                if attempts >= self._publish_retry_attempts:
                    record_billing_stream_event(source=source, result="failed")
                    raise
                await asyncio.sleep(self._publish_retry_delay_seconds)

        observe_stripe_webhook_event(event_type=message.event_type, result="broadcasted")
        result_label = "replayed" if source == "replay" else "published"
        record_billing_stream_event(source=source, result=result_label)
        logger.info(
            "Broadcasted billing event",
            extra={
                "tenant_id": message.tenant_id,
                "event_type": message.event_type,
                "stripe_event_id": message.stripe_event_id,
            },
        )

    async def mark_processed(self, processed_at: datetime | None) -> None:
        if not processed_at or not self._backend:
            return
        await self._backend.store_bookmark(self._bookmark_key, processed_at.isoformat())
        lag_seconds = (datetime.now(UTC) - processed_at).total_seconds()
        record_billing_stream_backlog(lag_seconds)

    async def subscribe(self, tenant_id: str) -> BillingEventStream:
        if not self._backend:
            raise RuntimeError("Billing events backend not configured.")
        return await self._backend.subscribe(self._channel(tenant_id))

    async def publish_raw(self, tenant_id: str, message: dict) -> None:
        """Test-only helper to inject events directly into the backend."""

        if not self._backend:
            raise RuntimeError("Billing events backend not configured.")
        await self._backend.publish(self._channel(tenant_id), json.dumps(message))

    async def list_history(
        self,
        *,
        tenant_id: str,
        limit: int = 25,
        cursor: str | None = None,
        event_type: str | None = None,
        status: StripeEventStatus | str | None = None,
    ) -> BillingEventHistoryPage:
        """Return a cursor-paginated slice of historical billing events."""

        if limit <= 0:
            raise ValueError("Limit must be positive.")

        repository = self._require_repository()
        cursor_values = self._decode_cursor(cursor) if cursor else None
        repo_status = status.value if isinstance(status, StripeEventStatus) else status
        page_size = max(1, limit)

        fetch_limit = page_size + 1
        events = await repository.list_tenant_events(
            tenant_id=tenant_id,
            limit=fetch_limit,
            cursor_received_at=cursor_values.received_at if cursor_values else None,
            cursor_event_id=cursor_values.event_id if cursor_values else None,
            event_type=event_type,
            status=repo_status,
        )

        trimmed_events = events[:page_size]

        payloads: list[BillingEventPayload] = []
        for record in trimmed_events:
            normalized = self._normalize_payload(record, record.payload, None)
            if normalized:
                payloads.append(normalized)

        next_cursor = None
        has_more = len(events) > page_size

        if has_more and trimmed_events:
            tail = trimmed_events[-1]
            next_cursor = self._encode_cursor(tail.received_at, tail.id)

        return BillingEventHistoryPage(items=payloads, next_cursor=next_cursor)

    def _channel(self, tenant_id: str) -> str:
        return f"{self._channel_prefix}{tenant_id}"

    def _require_repository(self) -> StripeEventRepository:
        if self._repository is None:
            raise RuntimeError(
                "StripeEventRepository is not configured for billing events service."
            )
        return self._repository

    def _derive_artifacts_from_payload(
        self, event_type: str, data_object: dict
    ) -> tuple[
        BillingEventSubscription | None,
        BillingEventInvoice | None,
        list[BillingEventUsage],
    ]:
        subscription = None
        invoice = None
        usage: list[BillingEventUsage] = []
        normalized_type = event_type or ""
        if normalized_type.startswith("customer.subscription"):
            subscription = self._subscription_payload_from_object(data_object)
        if normalized_type.startswith("invoice."):
            invoice = self._invoice_payload_from_object(data_object)
            usage = self._usage_from_invoice_object(data_object)
        return subscription, invoice, usage

    def _subscription_payload_from_object(
        self, data_obj: dict
    ) -> BillingEventSubscription | None:
        if not data_obj:
            return None
        plan_code = self._extract_plan_code(data_obj) or "unknown-plan"
        quantity = self._extract_quantity(data_obj)
        return BillingEventSubscription(
            plan_code=plan_code,
            status=str(data_obj.get("status") or "unknown"),
            seat_count=quantity,
            auto_renew=not bool(data_obj.get("cancel_at_period_end")),
            current_period_start=self._iso(
                self._coerce_datetime(data_obj.get("current_period_start"))
            ),
            current_period_end=self._iso(
                self._coerce_datetime(data_obj.get("current_period_end"))
            ),
            trial_ends_at=self._iso(self._coerce_datetime(data_obj.get("trial_end"))),
            cancel_at=self._iso(self._coerce_datetime(data_obj.get("cancel_at"))),
        )

    def _invoice_payload_from_object(self, invoice_obj: dict) -> BillingEventInvoice | None:
        if not invoice_obj:
            return None
        amount_due = invoice_obj.get("amount_due")
        if amount_due is None:
            amount_due = invoice_obj.get("total")
        amount_value = self._coerce_int(amount_due, default=0)
        return BillingEventInvoice(
            invoice_id=str(invoice_obj.get("id") or "invoice"),
            status=str(invoice_obj.get("status") or "unknown"),
            amount_due_cents=amount_value,
            currency=str(invoice_obj.get("currency") or "usd"),
            billing_reason=invoice_obj.get("billing_reason"),
            hosted_invoice_url=
                invoice_obj.get("hosted_invoice_url") or invoice_obj.get("invoice_pdf"),
            collection_method=invoice_obj.get("collection_method"),
            period_start=self._iso(self._coerce_datetime(invoice_obj.get("period_start"))),
            period_end=self._iso(self._coerce_datetime(invoice_obj.get("period_end"))),
        )

    def _usage_from_invoice_object(self, invoice_obj: dict) -> list[BillingEventUsage]:
        lines = ((invoice_obj.get("lines") or {}).get("data")) or []
        usage_entries: list[BillingEventUsage] = []
        for index, line in enumerate(lines):
            price = line.get("price") or {}
            recurring = price.get("recurring") or {}
            metadata = {
                **(price.get("metadata") or {}),
                **(line.get("metadata") or {}),
            }
            usage_type = recurring.get("usage_type")
            is_metered = usage_type == "metered" or bool(line.get("usage_record_summary"))
            if not is_metered:
                continue
            feature_key = (
                metadata.get("feature_key")
                or metadata.get("plan_feature")
                or price.get("nickname")
                or line.get("description")
                or f"feature-{index}"
            )
            quantity_raw = line.get("quantity")
            if quantity_raw in (None, 0):
                summary = line.get("usage_record_summary") or {}
                quantity_raw = summary.get("total_usage")
            quantity = self._maybe_int(quantity_raw)
            if quantity is None:
                continue
            period = line.get("period") or {}
            usage_entries.append(
                BillingEventUsage(
                    feature_key=str(feature_key),
                    quantity=quantity,
                    period_start=self._iso(self._coerce_datetime(period.get("start"))),
                    period_end=self._iso(self._coerce_datetime(period.get("end"))),
                    amount_cents=self._coerce_int(line.get("amount"), default=0),
                )
            )
        return usage_entries

    def _extract_plan_code(self, data_obj: dict) -> str | None:
        items = ((data_obj.get("items") or {}).get("data")) or []
        if items:
            price = items[0].get("price") or {}
            metadata = price.get("metadata") or {}
            return (
                metadata.get("plan_code")
                or metadata.get("starter_cli_plan_code")
                or price.get("nickname")
                or price.get("id")
            )
        plan = data_obj.get("plan") or {}
        metadata = plan.get("metadata") or {}
        return (
            metadata.get("plan_code")
            or metadata.get("starter_cli_plan_code")
            or plan.get("nickname")
            or plan.get("id")
        )

    def _extract_quantity(self, data_obj: dict) -> int | None:
        items = ((data_obj.get("items") or {}).get("data")) or []
        if items:
            quantity = items[0].get("quantity")
            quantity_val = self._maybe_int(quantity)
            if quantity_val is not None:
                return quantity_val
        quantity = data_obj.get("quantity")
        return self._maybe_int(quantity)

    def _encode_cursor(self, received_at: datetime, event_id: uuid.UUID) -> str:
        payload = json.dumps({"r": received_at.isoformat(), "e": str(event_id)})
        return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8")

    def _decode_cursor(self, token: str) -> _HistoryCursor:
        try:
            raw = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
            data = json.loads(raw)
            received_at = datetime.fromisoformat(str(data["r"]))
            event_id = uuid.UUID(str(data["e"]))
        except (KeyError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("Invalid cursor provided.") from exc
        return _HistoryCursor(received_at=received_at, event_id=event_id)

    def _normalize_payload(
        self,
        record: StripeEvent,
        payload: dict,
        context: DispatchBroadcastContext | None,
    ) -> BillingEventPayload | None:
        tenant_id = context.tenant_id if context else record.tenant_hint
        if tenant_id is None:
            return None
        data_object = (payload.get("data") or {}).get("object") or {}
        context_status = context.status if context else None
        context_summary = context.summary if context else None
        status = context_status or data_object.get("status") or data_object.get("billing_reason")
        summary = context_summary or data_object.get("description") or status
        occurred_at = record.processed_at or record.received_at
        subscription = None
        invoice = None
        usage: list[BillingEventUsage] = []
        if context:
            if context.subscription:
                subscription = self._subscription_payload_from_context(context.subscription)
            if context.invoice:
                invoice = self._invoice_payload_from_context(context.invoice)
            if context.usage:
                usage = [self._usage_payload_from_context(item) for item in context.usage]

        if subscription is None or invoice is None or not usage:
            (
                derived_subscription,
                derived_invoice,
                derived_usage,
            ) = self._derive_artifacts_from_payload(record.event_type, data_object)
            if subscription is None:
                subscription = derived_subscription
            if invoice is None:
                invoice = derived_invoice
            if not usage:
                usage = derived_usage
        return BillingEventPayload(
            tenant_id=tenant_id,
            event_type=record.event_type,
            stripe_event_id=record.stripe_event_id,
            occurred_at=(occurred_at or datetime.now(UTC)).isoformat(),
            summary=summary,
            status=status or record.processing_outcome,
            subscription=subscription,
            invoice=invoice,
            usage=usage,
        )

    def _subscription_payload_from_context(
        self, view: SubscriptionSnapshotView
    ) -> BillingEventSubscription:
        return BillingEventSubscription(
            plan_code=view.plan_code,
            status=view.status,
            seat_count=view.seat_count,
            auto_renew=view.auto_renew,
            current_period_start=self._iso(view.current_period_start),
            current_period_end=self._iso(view.current_period_end),
            trial_ends_at=self._iso(view.trial_ends_at),
            cancel_at=self._iso(view.cancel_at),
        )

    def _invoice_payload_from_context(self, view: InvoiceSnapshotView) -> BillingEventInvoice:
        return BillingEventInvoice(
            invoice_id=view.invoice_id,
            status=view.status,
            amount_due_cents=view.amount_due_cents,
            currency=view.currency,
            billing_reason=view.billing_reason,
            hosted_invoice_url=view.hosted_invoice_url,
            collection_method=view.collection_method,
            period_start=self._iso(view.period_start),
            period_end=self._iso(view.period_end),
        )

    def _usage_payload_from_context(self, usage: UsageDelta) -> BillingEventUsage:
        return BillingEventUsage(
            feature_key=usage.feature_key,
            quantity=usage.quantity,
            period_start=self._iso(usage.period_start),
            period_end=self._iso(usage.period_end),
            amount_cents=usage.amount_cents,
        )

    @staticmethod
    def _iso(value: datetime | None) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        else:
            value = value.astimezone(UTC)
        return value.isoformat()

    @staticmethod
    def _coerce_datetime(value: Any) -> datetime | None:
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=UTC)
            return value.astimezone(UTC)
        try:
            return datetime.fromtimestamp(float(value), tz=UTC)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _coerce_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _maybe_int(value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None


def get_billing_events_service() -> BillingEventsService:
    """Resolve the container-backed billing events service."""

    from app.bootstrap.container import get_container

    return get_container().billing_events_service


@dataclass(slots=True)
class _HistoryCursor:
    received_at: datetime
    event_id: uuid.UUID


class _BillingEventsServiceHandle:
    """Proxy exposing the configured billing events service."""

    def __getattr__(self, name: str):
        return getattr(get_billing_events_service(), name)


billing_events_service = _BillingEventsServiceHandle()
