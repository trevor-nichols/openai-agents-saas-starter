"""OpenAI Agents SDK runtime adapters implementing domain ports."""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from typing import Any

from agents import Runner
from agents.usage import Usage

from app.domain.ai import AgentRunResult, AgentRunUsage, AgentStreamEvent
from app.domain.ai.ports import (
    AgentRuntime,
    AgentSessionHandle,
    AgentStreamingHandle,
)
from openai.types.responses import ResponseTextDeltaEvent


def _convert_usage(usage: Usage | None) -> AgentRunUsage | None:
    if usage is None:
        return None
    return AgentRunUsage(
        input_tokens=int(usage.input_tokens) if usage.input_tokens is not None else None,
        output_tokens=int(usage.output_tokens) if usage.output_tokens is not None else None,
    )


def _coerce_delta(delta: Any) -> str:
    """Coerce SDK delta payloads into a string for streaming clients."""

    if delta is None:
        return ""
    if isinstance(delta, str):
        return delta
    try:
        return str(delta)
    except Exception:  # pragma: no cover - extremely defensive
        return ""


def _extract_agent_name(obj: Any) -> str | None:
    """Extract agent name from SDK agent or item structures."""

    if obj is None:
        return None
    name = getattr(obj, "name", None)
    if isinstance(name, str):
        return name
    # Some items carry agent on .agent
    agent = getattr(obj, "agent", None)
    agent_name = getattr(agent, "name", None)
    return agent_name if isinstance(agent_name, str) else None


def _extract_tool_info(item: Any) -> tuple[str | None, str | None]:
    """Best-effort extraction of tool call id/name from run items."""

    if item is None:
        return None, None
    raw_item = getattr(item, "raw_item", None)
    tool_call_id = getattr(raw_item, "id", None) or getattr(item, "id", None)
    tool_name = getattr(raw_item, "name", None) or getattr(item, "name", None)
    if tool_call_id is not None:
        tool_call_id = str(tool_call_id)
    if tool_name is not None:
        tool_name = str(tool_name)
    return tool_call_id, tool_name


class OpenAIStreamingHandle(AgentStreamingHandle):
    """Wraps the SDK streaming iterator to emit normalized events."""

    def __init__(self, *, stream, agent_key: str) -> None:
        self._stream = stream
        self._agent_key = agent_key

    async def events(self) -> AsyncIterator[AgentStreamEvent]:
        async for event in self._stream.stream_events():
            if event.type == "raw_response_event":
                raw = event.data
                raw_type = getattr(raw, "type", None)
                sequence_number = getattr(raw, "sequence_number", None)

                text_delta: str | None = None
                reasoning_delta: str | None = None

                if isinstance(raw, ResponseTextDeltaEvent):
                    text_delta = _coerce_delta(getattr(raw, "delta", None))
                elif raw_type in {"response.reasoning_text.delta", "response.reasoning_summary_text.delta"}:
                    reasoning_delta = _coerce_delta(getattr(raw, "delta", None))

                is_terminal = raw_type in {
                    "response.completed",
                    "response.incomplete",
                    "response.failed",
                }

                yield AgentStreamEvent(
                    kind="raw_response",
                    response_id=getattr(self._stream, "last_response_id", None),
                    sequence_number=sequence_number,
                    raw_type=raw_type,
                    text_delta=text_delta,
                    reasoning_delta=reasoning_delta,
                    is_terminal=is_terminal,
                    payload=AgentStreamEvent._to_mapping(raw),
                )

            elif event.type == "run_item_stream_event":
                item = getattr(event, "item", None)
                agent_name = _extract_agent_name(item)
                tool_call_id, tool_name = _extract_tool_info(item)

                yield AgentStreamEvent(
                    kind="run_item",
                    response_id=getattr(self._stream, "last_response_id", None),
                    run_item_name=getattr(event, "name", None),
                    run_item_type=getattr(item, "type", None),
                    agent=agent_name,
                    tool_call_id=tool_call_id,
                    tool_name=tool_name,
                    is_terminal=False,
                    payload=AgentStreamEvent._to_mapping(item),
                )

            elif event.type == "agent_updated_stream_event":
                new_agent = getattr(event, "new_agent", None)
                yield AgentStreamEvent(
                    kind="agent_update",
                    response_id=getattr(self._stream, "last_response_id", None),
                    new_agent=_extract_agent_name(new_agent),
                    payload=AgentStreamEvent._to_mapping(new_agent),
                )

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
        # Tests often mock Runner.run to return our domain AgentRunResult directly;
        # support both the SDK response shape and the domain model to keep the
        # runtime resilient to test doubles.
        if isinstance(result, AgentRunResult):
            usage = result.usage
            response_id = result.response_id
            final_output = result.final_output
        else:
            context = getattr(result, "context_wrapper", None)
            usage = _convert_usage(getattr(context, "usage", None) if context else None)
            response_id = getattr(result, "last_response_id", None)
            final_output = getattr(result, "final_output", "")
        base_metadata: dict[str, Any] = {"agent_key": agent_key, "model": str(agent.model)}
        metadata_payload: Mapping[str, Any]
        if metadata:
            metadata_payload = {**base_metadata, **dict(metadata)}
        else:
            metadata_payload = base_metadata
        return AgentRunResult(
            final_output=str(final_output),
            response_id=response_id,
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
