"""Lifecycle hook plumbing between the SDK and domain stream events."""

from __future__ import annotations

from typing import Any

from agents import Agent
from agents.lifecycle import RunHooksBase

from app.domain.ai.lifecycle import LifecycleEventBus as _LifecycleEventBus
from app.domain.ai.lifecycle import LifecycleEventSink as _LifecycleEventSink
from app.domain.ai.models import AgentStreamEvent

from .tool_calls import extract_agent_name

LifecycleEventBus = _LifecycleEventBus
LifecycleEventSink = _LifecycleEventSink


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
