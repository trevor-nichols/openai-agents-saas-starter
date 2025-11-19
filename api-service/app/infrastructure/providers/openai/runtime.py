"""OpenAI Agents SDK runtime adapters implementing domain ports."""

from __future__ import annotations

from typing import Any, AsyncIterator, Mapping

from agents import Runner
from agents.usage import Usage
from openai.types.responses import ResponseTextDeltaEvent

from app.domain.ai import AgentRunResult, AgentRunUsage, AgentStreamEvent
from app.domain.ai.ports import (
    AgentRuntime,
    AgentSessionHandle,
    AgentStreamingHandle,
)


def _convert_usage(usage: Usage | None) -> AgentRunUsage | None:
    if usage is None:
        return None
    return AgentRunUsage(
        input_tokens=int(usage.input_tokens) if usage.input_tokens is not None else None,
        output_tokens=int(usage.output_tokens) if usage.output_tokens is not None else None,
    )


class OpenAIStreamingHandle(AgentStreamingHandle):
    """Wraps the SDK streaming iterator to emit normalized events."""

    def __init__(self, *, stream, agent_key: str) -> None:
        self._stream = stream
        self._agent_key = agent_key

    async def events(self) -> AsyncIterator[AgentStreamEvent]:
        async for event in self._stream.stream_events():
            if event.type == "raw_response_event" and isinstance(
                event.data, ResponseTextDeltaEvent
            ):
                delta = getattr(event.data, "delta", "")
                # ResponseTextDeltaEvent.delta may be a structured delta; coerce to text
                if delta is None:
                    chunk = ""
                elif isinstance(delta, str):
                    chunk = delta
                else:  # pragma: no cover - defensive stringify for nested delta objects
                    chunk = str(delta)
                yield AgentStreamEvent(content_delta=chunk)
            elif event.type == "run_item_stream_event" and (
                event.item.type == "message_output_item"
            ):
                yield AgentStreamEvent(content_delta="", is_terminal=True)

    @property
    def last_response_id(self) -> str | None:  # pragma: no cover - passthrough
        return getattr(self._stream, "last_response_id", None)

    @property
    def usage(self) -> AgentRunUsage | None:  # pragma: no cover - passthrough
        context = getattr(self._stream, "context_wrapper", None)
        if not context:
            return None
        return _convert_usage(getattr(context, "usage", None))


class OpenAIAgentRuntime(AgentRuntime):
    """Executes OpenAI Agents leveraging the shared registry."""

    def __init__(self, registry) -> None:
        self._registry = registry

    async def run(
        self,
        agent_key: str,
        message: str,
        *,
        session: AgentSessionHandle | None = None,
        conversation_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> AgentRunResult:
        agent = self._registry.get_agent_handle(agent_key)
        if agent is None:
            raise ValueError(f"Agent '{agent_key}' is not registered for OpenAI provider")
        result = await Runner.run(
            agent,
            message,
            session=session,
            conversation_id=conversation_id,
        )
        context = getattr(result, "context_wrapper", None)
        usage = _convert_usage(getattr(context, "usage", None) if context else None)
        base_metadata: dict[str, Any] = {"agent_key": agent_key, "model": str(agent.model)}
        metadata_payload: Mapping[str, Any]
        if metadata:
            metadata_payload = {**base_metadata, **dict(metadata)}
        else:
            metadata_payload = base_metadata
        return AgentRunResult(
            final_output=str(result.final_output),
            response_id=result.last_response_id,
            usage=usage,
            metadata=metadata_payload,
        )

    def run_stream(
        self,
        agent_key: str,
        message: str,
        *,
        session: AgentSessionHandle | None = None,
        conversation_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> AgentStreamingHandle:
        agent = self._registry.get_agent_handle(agent_key)
        if agent is None:
            raise ValueError(f"Agent '{agent_key}' is not registered for OpenAI provider")
        stream = Runner.run_streamed(
            agent,
            message,
            session=session,
            conversation_id=conversation_id,
        )
        # Metadata isn't consumed directly for streams, but maintained for parity.
        _ = metadata
        return OpenAIStreamingHandle(stream=stream, agent_key=agent_key)


__all__ = ["OpenAIAgentRuntime", "OpenAIStreamingHandle"]
