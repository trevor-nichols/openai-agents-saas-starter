"""Billing event broadcasting and streaming helpers."""

from __future__ import annotations

import asyncio
import json
import logging
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import AsyncIterator, Protocol

from redis.asyncio import Redis

from app.infrastructure.persistence.stripe.models import StripeEvent
from app.infrastructure.persistence.stripe.repository import StripeEventRepository
from app.observability.metrics import observe_stripe_webhook_event

logger = logging.getLogger("anything-agents.services.billing_events")


@dataclass(slots=True)
class BillingEventPayload:
    tenant_id: str
    event_type: str
    stripe_event_id: str
    occurred_at: str
    summary: str | None
    status: str


class BillingEventStream(Protocol):
    async def next_message(self, timeout: float | None = None) -> str | None:
        ...

    async def close(self) -> None:
        ...


class BillingEventBackend(Protocol):
    async def publish(self, channel: str, message: str) -> None:
        ...

    async def subscribe(self, channel: str) -> BillingEventStream:
        ...

    async def store_bookmark(self, key: str, value: str) -> None:
        ...

    async def load_bookmark(self, key: str) -> str | None:
        ...

    async def close(self) -> None:
        ...


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
                replay_after = event.processed_at or datetime.now(timezone.utc)
            if replay_after is not None:
                await self.mark_processed(replay_after)

    async def publish_from_event(self, record: StripeEvent, payload: dict) -> None:
        if not self._enabled or not self._backend:
            return
        if not record.tenant_hint:
            logger.debug("Skipping Stripe event %s without tenant hint", record.stripe_event_id)
            return
        await self._publish(record, payload)

    async def _publish_from_record(self, record: StripeEvent) -> None:
        await self._publish(record, record.payload)
        await self.mark_processed(record.processed_at)

    async def _publish(self, record: StripeEvent, payload: dict) -> None:
        if not record.tenant_hint or not self._backend:
            return
        message = self._normalize_payload(record, payload)
        if message is None:
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
                observe_stripe_webhook_event(event_type=message.event_type, result="broadcast_failed")
                if attempts >= self._publish_retry_attempts:
                    raise
                await asyncio.sleep(self._publish_retry_delay_seconds)

        observe_stripe_webhook_event(event_type=message.event_type, result="broadcasted")
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

    def _normalize_payload(self, record: StripeEvent, payload: dict) -> BillingEventPayload | None:
        tenant_id = record.tenant_hint
        if tenant_id is None:
            return None
        data_object = (payload.get("data") or {}).get("object") or {}
        status = data_object.get("status") or data_object.get("billing_reason")
        summary = data_object.get("description") or status
        occurred_at = record.processed_at or record.received_at
        return BillingEventPayload(
            tenant_id=tenant_id,
            event_type=record.event_type,
            stripe_event_id=record.stripe_event_id,
            occurred_at=(occurred_at or datetime.now(timezone.utc)).isoformat(),
            summary=summary,
            status=record.processing_outcome,
        )


_billing_events_service = BillingEventsService()


def configure_billing_events_service(service: BillingEventsService) -> None:
    global _billing_events_service
    _billing_events_service = service


def get_billing_events_service() -> BillingEventsService:
    return _billing_events_service


billing_events_service = _billing_events_service
