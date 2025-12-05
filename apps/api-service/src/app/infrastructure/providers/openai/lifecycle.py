"""Lifecycle hook plumbing between the SDK and domain stream events."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterable
from typing import Any, Protocol, runtime_checkable

from agents import Agent
from agents.lifecycle import RunHooksBase

from app.domain.ai.models import AgentStreamEvent

from .tool_calls import extract_agent_name


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


class HookRelay(RunHooksBase[Any, Agent[Any]]):
    """Bridge SDK RunHooks events into AgentStreamEvent lifecycle messages."""

    def __init__(self, bus: LifecycleEventSink) -> None:
        self._bus = bus

    async def on_agent_start(self, context, agent):
        await self._bus.emit(
            AgentStreamEvent(kind="lifecycle", event="agent_start", agent=extract_agent_name(agent))
        )

    async def on_agent_end(self, context, agent, output):
        await self._bus.emit(
            AgentStreamEvent(kind="lifecycle", event="agent_end", agent=extract_agent_name(agent))
        )

    async def on_handoff(self, context, from_agent, to_agent):
        await self._bus.emit(
            AgentStreamEvent(
                kind="lifecycle",
                event="handoff",
                agent=extract_agent_name(from_agent),
                new_agent=extract_agent_name(to_agent),
            )
        )

    async def on_tool_start(self, context, agent, tool):
        await self._bus.emit(
            AgentStreamEvent(
                kind="lifecycle",
                event="tool_start",
                agent=extract_agent_name(agent),
                tool_name=getattr(tool, "name", None),
            )
        )

    async def on_tool_end(self, context, agent, tool, result):
        await self._bus.emit(
            AgentStreamEvent(
                kind="lifecycle",
                event="tool_end",
                agent=extract_agent_name(agent),
                tool_name=getattr(tool, "name", None),
            )
        )

    async def on_llm_start(self, context, agent, system_prompt, input_items):
        await self._bus.emit(
            AgentStreamEvent(kind="lifecycle", event="llm_start", agent=extract_agent_name(agent))
        )

    async def on_llm_end(self, context, agent, response):
        await self._bus.emit(
            AgentStreamEvent(kind="lifecycle", event="llm_end", agent=extract_agent_name(agent))
        )


__all__ = ["LifecycleEventBus", "LifecycleEventSink", "HookRelay"]
