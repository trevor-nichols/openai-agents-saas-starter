"""Domain-level lifecycle event plumbing.

Providers and orchestration services sometimes need a lightweight sink for
streaming lifecycle events (handoffs, tool boundaries, memory compaction, etc.).

This module lives in the domain layer so application services can depend on it
without importing provider-specific infrastructure code.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterable
from typing import Protocol, runtime_checkable

from app.domain.ai.models import AgentStreamEvent


@runtime_checkable
class LifecycleEventSink(Protocol):
    async def emit(self, event: AgentStreamEvent) -> None: ...

    def drain(self) -> AsyncIterable[AgentStreamEvent]: ...


class LifecycleEventBus:
    """Lightweight async queue for lifecycle events emitted by hooks."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[AgentStreamEvent] = asyncio.Queue()

    async def emit(self, event: AgentStreamEvent) -> None:
        await self._queue.put(event)

    def drain(self) -> AsyncIterable[AgentStreamEvent]:
        async def _gen():
            while not self._queue.empty():
                yield await self._queue.get()

        return _gen()


__all__ = ["LifecycleEventBus", "LifecycleEventSink"]

