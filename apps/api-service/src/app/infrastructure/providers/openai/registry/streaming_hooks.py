"""Helpers to bridge agent-tool stream events into the public pipeline."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from agents import Agent

from app.domain.ai import StreamEventBus, StreamScope
from app.domain.ai.models import AgentStreamEvent

from ..stream_event_mapper import map_stream_event
from ..tool_calls import extract_agent_name

AgentToolStreamHandler = Callable[[Any], Awaitable[None]] | None


def build_agent_tool_stream_handler(
    *,
    tool_stream_bus: StreamEventBus | None,
    tool_name: str,
    target_agent: Agent,
    tool_stream_metadata: Mapping[str, Any] | None = None,
) -> AgentToolStreamHandler:
    if tool_stream_bus is None:
        return None

    async def _on_stream(tool_event: Any) -> None:
        stream_event = getattr(tool_event, "event", None)
        if stream_event is None:
            return
        tool_call_id, tool_call_name = _extract_tool_call_info(
            getattr(tool_event, "tool_call", None)
        )
        if not tool_call_id:
            return
        response_id = getattr(stream_event, "response_id", None)
        mapped = map_stream_event(
            stream_event,
            response_id=response_id,
            metadata=tool_stream_metadata,
        )
        if mapped is None:
            return

        agent_name = extract_agent_name(getattr(tool_event, "agent", None)) or extract_agent_name(
            target_agent
        )
        mapped.scope = StreamScope(
            type="agent_tool",
            tool_call_id=tool_call_id,
            tool_name=tool_call_name or tool_name,
            agent=agent_name,
        )
        mapped.agent = None
        await tool_stream_bus.emit(mapped)

    return _on_stream


def _extract_tool_call_info(tool_call: Any) -> tuple[str | None, str | None]:
    tool_call_map = AgentStreamEvent._to_mapping(tool_call)
    if not isinstance(tool_call_map, Mapping):
        return None, None
    call_id = tool_call_map.get("id") or tool_call_map.get("call_id")
    name = tool_call_map.get("name")
    call_id_str = str(call_id) if call_id is not None else None
    name_str = str(name) if isinstance(name, str) and name else None
    return call_id_str, name_str


__all__ = ["build_agent_tool_stream_handler"]
