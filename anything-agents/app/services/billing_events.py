"""Billing event broadcasting and streaming helpers."""

from __future__ import annotations

import asyncio
import json
import logging
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Protocol

from redis.asyncio import Redis

from app.infrastructure.persistence.stripe.models import StripeEvent
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
        backend: BillingEventBackend,
        repository: StripeEventRepository | None,
    ) -> None:
        self._backend = backend
        self._repository = repository
        self._enabled = True

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
        if not record.tenant_hint:
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
        if not record.tenant_hint or not self._backend:
            record_billing_stream_event(source=source, result="skipped_backend")
            return
        message = self._normalize_payload(record, payload, context)
        if message is None:
            record_billing_stream_event(source=source, result="normalization_failed")
            return
        channel = self._channel(record.tenant_hint)
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

    def _channel(self, tenant_id: str) -> str:
        return f"{self._channel_prefix}{tenant_id}"

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


_billing_events_service = BillingEventsService()


def configure_billing_events_service(service: BillingEventsService) -> None:
    global _billing_events_service
    _billing_events_service = service


def get_billing_events_service() -> BillingEventsService:
    return _billing_events_service


billing_events_service = _billing_events_service
