"""Async queue-backed billing event backend for tests."""

from __future__ import annotations

import asyncio
from collections import defaultdict

from app.services.billing_events import BillingEventBackend, BillingEventStream


class QueueBillingEventStream(BillingEventStream):
    def __init__(self, queue: asyncio.Queue[str]) -> None:
        self._queue = queue
        self._closed = False
        self._pending: asyncio.Task[str | None] | None = None

    async def next_message(self, timeout: float | None = None) -> str | None:
        if self._closed:
            return None
        if timeout is None:
            return await self._queue.get()
        try:
            self._pending = asyncio.create_task(self._queue.get())
            return await asyncio.wait_for(self._pending, timeout=timeout)
        except TimeoutError:
            return None
        finally:
            if self._pending and not self._pending.done():
                self._pending.cancel()
            self._pending = None

    async def close(self) -> None:
        self._closed = True
        if self._pending and not self._pending.done():
            self._pending.cancel()


class QueueBillingEventBackend(BillingEventBackend):
    def __init__(self) -> None:
        self._queues: defaultdict[str, asyncio.Queue[str]] = defaultdict(asyncio.Queue)
        self._bookmarks: dict[str, str] = {}
        self._subscribers: set[QueueBillingEventStream] = set()

    async def publish(self, channel: str, message: str) -> None:
        print(f"fake_backend publish {channel} -> {message}")
        await self._queues[channel].put(message)

    async def subscribe(self, channel: str) -> BillingEventStream:
        print(f"fake_backend subscribe {channel}")
        stream = QueueBillingEventStream(self._queues[channel])
        self._subscribers.add(stream)
        return stream

    async def store_bookmark(self, key: str, value: str) -> None:
        self._bookmarks[key] = value

    async def load_bookmark(self, key: str) -> str | None:
        return self._bookmarks.get(key)

    async def close(self) -> None:
        self._queues.clear()
        self._bookmarks.clear()
        for stream in list(self._subscribers):
            await stream.close()
        self._subscribers.clear()
