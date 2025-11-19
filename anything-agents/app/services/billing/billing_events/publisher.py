"""Publishing logic for billing events."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import asdict
from datetime import UTC, datetime

from app.infrastructure.persistence.stripe.models import StripeEvent
from app.infrastructure.persistence.stripe.repository import StripeEventRepository
from app.observability.metrics import (
    observe_stripe_webhook_event,
    record_billing_stream_backlog,
    record_billing_stream_event,
)
from app.services.billing.stripe.event_models import DispatchBroadcastContext

from .normalizer import BillingEventNormalizer
from .protocols import BillingEventBackend
from .types import JSONDict

logger = logging.getLogger("anything-agents.services.billing_events.publisher")


class BillingEventPublisher:
    def __init__(
        self,
        *,
        normalizer: BillingEventNormalizer,
        channel_prefix: str = "billing:events:tenant:",
        bookmark_key: str = "billing:events:last_processed_at",
        publish_retry_attempts: int = 3,
        publish_retry_delay_seconds: float = 0.25,
    ) -> None:
        self._normalizer = normalizer
        self._backend: BillingEventBackend | None = None
        self._repository: StripeEventRepository | None = None
        self._channel_prefix = channel_prefix
        self._bookmark_key = bookmark_key
        self._enabled = False
        self._publish_retry_attempts = publish_retry_attempts
        self._publish_retry_delay_seconds = publish_retry_delay_seconds

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

    async def publish_from_event(
        self,
        record: StripeEvent,
        payload: JSONDict,
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

    async def mark_processed(self, processed_at: datetime | None) -> None:
        if not processed_at or not self._backend:
            return
        await self._backend.store_bookmark(self._bookmark_key, processed_at.isoformat())
        lag_seconds = (datetime.now(UTC) - processed_at).total_seconds()
        record_billing_stream_backlog(lag_seconds)

    async def subscribe(self, tenant_id: str):
        if not self._backend:
            raise RuntimeError("Billing events backend not configured.")
        return await self._backend.subscribe(self._channel(tenant_id))

    async def publish_raw(self, tenant_id: str, message: JSONDict) -> None:
        if not self._backend:
            raise RuntimeError("Billing events backend not configured.")
        await self._backend.publish(self._channel(tenant_id), json.dumps(message))

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

    async def _publish_from_record(self, record: StripeEvent) -> None:
        await self._publish(record, record.payload, None, source="replay")
        await self.mark_processed(record.processed_at)

    async def _publish(
        self,
        record: StripeEvent,
        payload: JSONDict,
        context: DispatchBroadcastContext | None,
        *,
        source: str,
    ) -> None:
        if not self._backend:
            record_billing_stream_event(source=source, result="skipped_backend")
            return
        message = self._normalizer.normalize(record, payload, context)
        if message is None:
            record_billing_stream_event(source=source, result="normalization_failed")
            return
        channel = self._channel(message.tenant_id)
        attempts = 0
        while True:
            try:
                await self._backend.publish(channel, json.dumps(asdict(message)))
                break
            except Exception as exc:  # pragma: no cover - failure path exercised via mocks
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

    def _channel(self, tenant_id: str) -> str:
        return f"{self._channel_prefix}{tenant_id}"
