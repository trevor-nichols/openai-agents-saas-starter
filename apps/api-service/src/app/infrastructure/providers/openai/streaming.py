"""Streaming adapter that normalizes OpenAI SDK events into AgentStreamEvent."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Mapping
from typing import Any

from app.domain.ai import AgentRunUsage, AgentStreamEvent, AgentStreamingHandle, StreamEventBus

from .lifecycle import LifecycleEventSink
from .stream_event_mapper import map_stream_event
from .usage import convert_usage


class OpenAIStreamingHandle(AgentStreamingHandle):
    """Wraps the SDK streaming iterator to emit normalized events."""

    def __init__(
        self,
        *,
        stream,
        agent_key: str,
        metadata: Mapping[str, Any],
        lifecycle_bus: LifecycleEventSink | None = None,
        tool_stream_bus: StreamEventBus | None = None,
    ) -> None:
        self._stream = stream
        self._agent_key = agent_key
        self.metadata = metadata
        self._lifecycle_bus = lifecycle_bus
        self._tool_stream_bus = tool_stream_bus

    async def events(self) -> AsyncIterator[AgentStreamEvent]:
        if self._lifecycle_bus:
            async for ev in self._lifecycle_bus.drain():
                yield ev
        if self._tool_stream_bus:
            async for ev in self._tool_stream_bus.drain():
                yield ev

        async for event in self._stream.stream_events():
            async for mapped in self._map_event(event):
                yield mapped
            if self._lifecycle_bus:
                async for ev in self._lifecycle_bus.drain():
                    yield ev
            if self._tool_stream_bus:
                async for ev in self._tool_stream_bus.drain():
                    yield ev

        if self._tool_stream_bus:
            async for ev in self._tool_stream_bus.drain():
                yield ev

        # Emit a final structured-output event once the stream is complete.
        final_output = getattr(self._stream, "final_output", None)
        response_id = getattr(self._stream, "last_response_id", None)
        structured_output = None
        response_text = None
        if final_output is not None:
            if isinstance(final_output, str):
                response_text = final_output
            else:
                structured_output = final_output
                try:
                    response_text = json.dumps(final_output, ensure_ascii=False)
                except Exception:  # pragma: no cover
                    response_text = str(final_output)
        yield AgentStreamEvent(
            kind="run_item_stream_event",
            response_id=response_id,
            is_terminal=True,
            payload={"structured_output": structured_output, "response_text": response_text},
            structured_output=structured_output,
            response_text=response_text,
            usage=self.usage,
            metadata=self.metadata,
            agent=self._agent_key,
        )

    async def _map_event(self, event) -> AsyncIterator[AgentStreamEvent]:
        mapped = map_stream_event(
            event,
            response_id=getattr(self._stream, "last_response_id", None),
            metadata=self.metadata,
        )
        if mapped:
            yield mapped

    @property
    def last_response_id(self) -> str | None:  # pragma: no cover - passthrough
        return getattr(self._stream, "last_response_id", None)

    @property
    def usage(self) -> AgentRunUsage | None:  # pragma: no cover - passthrough
        context = getattr(self._stream, "context_wrapper", None)
        if not context:
            return None
        return convert_usage(getattr(context, "usage", None))


__all__ = ["OpenAIStreamingHandle"]
