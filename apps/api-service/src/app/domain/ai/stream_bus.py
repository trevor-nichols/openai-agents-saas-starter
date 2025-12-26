"""Async event bus for nested agent stream events."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterable
from typing import Protocol, runtime_checkable

from app.domain.ai.models import AgentStreamEvent


@runtime_checkable
class StreamEventSink(Protocol):
    async def emit(self, event: AgentStreamEvent) -> None: ...

    def drain(self) -> AsyncIterable[AgentStreamEvent]: ...


class StreamEventBus:
    """Lightweight async queue for nested stream events."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[AgentStreamEvent] = asyncio.Queue()

    async def emit(self, event: AgentStreamEvent) -> None:
        await self._queue.put(event)

    def drain(self) -> AsyncIterable[AgentStreamEvent]:
        async def _gen():
            while not self._queue.empty():
                yield await self._queue.get()

        return _gen()


__all__ = ["StreamEventBus", "StreamEventSink"]
