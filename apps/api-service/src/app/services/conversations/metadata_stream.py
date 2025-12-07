"""Lightweight in-memory pubsub for conversation metadata events (e.g., titles)."""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from collections.abc import AsyncIterator
from datetime import UTC, datetime

SubscriberKey = tuple[str, str]  # (tenant_id, conversation_id)
EventPayload = dict[str, object]

_subscribers: dict[SubscriberKey, list[asyncio.Queue[EventPayload]]] = defaultdict(list)
_lock = asyncio.Lock()


async def publish(
    *,
    tenant_id: str,
    conversation_id: str,
    event: EventPayload,
) -> None:
    """Publish a metadata event to all subscribers for the conversation."""

    key = (tenant_id, conversation_id)
    async with _lock:
        queues: list[asyncio.Queue[EventPayload]] = list(_subscribers.get(key, []))

    if not queues:
        return

    for queue in queues:
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            # Drop if overwhelmed; metadata events are best-effort.
            continue


async def subscribe(
    *,
    tenant_id: str,
    conversation_id: str,
) -> AsyncIterator[str]:
    """Yield JSON-encoded events for the given conversation until cancelled."""

    queue: asyncio.Queue[EventPayload] = asyncio.Queue()
    key = (tenant_id, conversation_id)

    async with _lock:
        _subscribers[key].append(queue)

    try:
        while True:
            event = await queue.get()
            if "timestamp" not in event:
                event["timestamp"] = datetime.now(UTC).isoformat()
            yield json.dumps(event, default=str)
    finally:
        async with _lock:
            subs = _subscribers.get(key, [])
            if queue in subs:
                subs.remove(queue)
            if not subs and key in _subscribers:
                _subscribers.pop(key, None)


__all__ = ["publish", "subscribe"]
