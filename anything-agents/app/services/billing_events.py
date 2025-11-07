"""Billing event broadcasting and streaming helpers."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import AsyncIterator, Protocol

from redis.asyncio import Redis

from app.infrastructure.persistence.stripe.models import StripeEvent
from app.infrastructure.persistence.stripe.repository import StripeEventRepository, StripeEventStatus
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
    def __init__(self, pubsub, channel: str) -> None:
        self._pubsub = pubsub
        self._channel = channel
        self._closed = False

    async def next_message(self, timeout: float | None = None) -> str | None:
        if self._closed:
            return None
        poll_timeout = timeout or 1.0
        elapsed = 0.0
        interval = min(poll_timeout, 1.0)
        while not self._closed:
            message = await self._pubsub.get_message(ignore_subscribe_messages=True, timeout=interval)
            if message and message.get("type") == "message":
                data = message.get("data")
                if isinstance(data, bytes):
                    return data.decode("utf-8")
                return str(data)
            elapsed += interval
            if timeout and elapsed >= timeout:
                return None
        return None

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            await self._pubsub.unsubscribe(self._channel)
        finally:
            await self._pubsub.close()


class RedisBillingEventBackend:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def publish(self, channel: str, message: str) -> None:
        await self._redis.publish(channel, message)

    async def subscribe(self, channel: str) -> BillingEventStream:
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(channel)
        return RedisBillingEventStream(pubsub, channel)

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


class InMemoryBillingEventStream:
    def __init__(self, queue: "asyncio.Queue[str]") -> None:
        self._queue = queue
        self._closed = False

    async def next_message(self, timeout: float | None = None) -> str | None:
        if self._closed:
            return None
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def close(self) -> None:
        self._closed = True


class InMemoryBillingEventBackend:
    def __init__(self) -> None:
        self._queues: dict[str, asyncio.Queue[str]] = {}
        self._bookmark: str | None = None

    def _queue(self, channel: str) -> asyncio.Queue[str]:
        if channel not in self._queues:
            self._queues[channel] = asyncio.Queue()
        return self._queues[channel]

    async def publish(self, channel: str, message: str) -> None:
        await self._queue(channel).put(message)

    async def subscribe(self, channel: str) -> BillingEventStream:
        return InMemoryBillingEventStream(self._queue(channel))

    async def store_bookmark(self, key: str, value: str) -> None:
        self._bookmark = value

    async def load_bookmark(self, key: str) -> str | None:
        return self._bookmark

    async def close(self) -> None:
        self._queues.clear()


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
