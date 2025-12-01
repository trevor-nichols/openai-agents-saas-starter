"""OpenAI Agents SDK runtime adapters implementing domain ports."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterable, AsyncIterator, Mapping
from typing import Any, Protocol, cast, runtime_checkable

from agents import Agent, Runner
from agents.lifecycle import RunHooksBase
from agents.run import RunConfig
from agents.usage import Usage

from app.agents._shared.handoff_filters import get_filter as get_handoff_filter
from app.agents._shared.prompt_context import PromptRuntimeContext
from app.core.settings import get_settings
from app.domain.ai import AgentRunResult, AgentRunUsage, AgentStreamEvent, RunOptions
from app.domain.ai.ports import (
    AgentRuntime,
    AgentSessionHandle,
    AgentStreamingHandle,
)
from app.services.agents.context import ConversationActorContext
from openai.types.responses import ResponseTextDeltaEvent

logger = logging.getLogger(__name__)


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
        """Async generator to drain queued events without blocking."""

        async def _gen():
            while not self._queue.empty():
                yield await self._queue.get()

        return _gen()


class _HookRelay(RunHooksBase[Any, Agent[Any]]):
    """Bridges SDK RunHooks events into AgentStreamEvent lifecycle messages."""

    def __init__(self, bus: LifecycleEventSink) -> None:
        self._bus = bus

    async def on_agent_start(self, context, agent):
        await self._bus.emit(
            AgentStreamEvent(
                kind="lifecycle",
                event="agent_start",
                agent=_extract_agent_name(agent),
            )
        )

    async def on_agent_end(self, context, agent, output):
        await self._bus.emit(
            AgentStreamEvent(kind="lifecycle", event="agent_end", agent=_extract_agent_name(agent))
        )

    async def on_handoff(self, context, from_agent, to_agent):
        await self._bus.emit(
            AgentStreamEvent(
                kind="lifecycle",
                event="handoff",
                agent=_extract_agent_name(from_agent),
                new_agent=_extract_agent_name(to_agent),
            )
        )

    async def on_tool_start(self, context, agent, tool):
        await self._bus.emit(
            AgentStreamEvent(
                kind="lifecycle",
                event="tool_start",
                agent=_extract_agent_name(agent),
                tool_name=getattr(tool, "name", None),
            )
        )

    async def on_tool_end(self, context, agent, tool, result):
        await self._bus.emit(
            AgentStreamEvent(
                kind="lifecycle",
                event="tool_end",
                agent=_extract_agent_name(agent),
                tool_name=getattr(tool, "name", None),
            )
        )

    async def on_llm_start(self, context, agent, system_prompt, input_items):
        await self._bus.emit(
            AgentStreamEvent(kind="lifecycle", event="llm_start", agent=_extract_agent_name(agent))
        )

    async def on_llm_end(self, context, agent, response):
        await self._bus.emit(
            AgentStreamEvent(kind="lifecycle", event="llm_end", agent=_extract_agent_name(agent))
        )


class OpenAIStreamingHandle(AgentStreamingHandle):
    """Wraps the SDK streaming iterator to emit normalized events."""

    def __init__(
        self,
        *,
        stream,
        agent_key: str,
        metadata: Mapping[str, Any],
        lifecycle_bus: LifecycleEventSink | None = None,
    ) -> None:
        self._stream = stream
        self._agent_key = agent_key
        self.metadata = metadata
        self._lifecycle_bus = lifecycle_bus

    async def events(self) -> AsyncIterator[AgentStreamEvent]:
        if self._lifecycle_bus:
            async for ev in self._lifecycle_bus.drain():
                yield ev
        async for event in self._stream.stream_events():
            if event.type == "raw_response_event":
                raw = event.data
                raw_type = getattr(raw, "type", None)
                sequence_number = getattr(raw, "sequence_number", None)

                text_delta: str | None = None
                reasoning_delta: str | None = None

                if isinstance(raw, ResponseTextDeltaEvent):
                    text_delta = _coerce_delta(getattr(raw, "delta", None))
                elif raw_type in {
                    "response.reasoning_text.delta",
                    "response.reasoning_summary_text.delta",
                }:
                    reasoning_delta = _coerce_delta(getattr(raw, "delta", None))

                yield AgentStreamEvent(
                    kind="raw_response",
                    response_id=getattr(self._stream, "last_response_id", None),
                    sequence_number=sequence_number,
                    raw_type=raw_type,
                    text_delta=text_delta,
                    reasoning_delta=reasoning_delta,
                    is_terminal=False,  # defer terminal until structured-output flush
                    payload=AgentStreamEvent._to_mapping(raw),
                    metadata=self.metadata,
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
                    metadata=self.metadata,
                )

            elif event.type == "agent_updated_stream_event":
                new_agent = getattr(event, "new_agent", None)
                yield AgentStreamEvent(
                    kind="agent_update",
                    response_id=getattr(self._stream, "last_response_id", None),
                    new_agent=_extract_agent_name(new_agent),
                    payload=AgentStreamEvent._to_mapping(new_agent),
                    metadata=self.metadata,
                )
            if self._lifecycle_bus:
                async for ev in self._lifecycle_bus.drain():
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
                kind="run_item",
                response_id=response_id,
                is_terminal=True,
                payload={"structured_output": structured_output, "response_text": response_text},
                structured_output=structured_output,
                response_text=response_text,
                metadata=self.metadata,
                agent=self._agent_key,
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
        self._bootstrap_ctx = PromptRuntimeContext(
            actor=ConversationActorContext(
                tenant_id="bootstrap-tenant",
                user_id="bootstrap-user",
            ),
            conversation_id="bootstrap",
            request_message="",
            settings=get_settings(),
        )

    async def run(
        self,
        agent_key: str,
        message: str,
        *,
        session: AgentSessionHandle | None = None,
        conversation_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        options: RunOptions | None = None,
    ) -> AgentRunResult:
        runtime_ctx = None
        safe_metadata: dict[str, Any] = {}
        if metadata and isinstance(metadata, Mapping):
            runtime_ctx = metadata.get("prompt_runtime_ctx")
            safe_metadata = {k: v for k, v in metadata.items() if k != "prompt_runtime_ctx"}
        if runtime_ctx is None:
            runtime_ctx = self._bootstrap_ctx
        elif not isinstance(runtime_ctx, PromptRuntimeContext):
            raise TypeError("prompt_runtime_ctx must be a PromptRuntimeContext")
        agent = self._registry.get_agent_handle(
            agent_key,
            runtime_ctx=runtime_ctx,
            validate_prompts=True,
        )
        if agent is None:
            raise ValueError(f"Agent '{agent_key}' is not registered for OpenAI provider")
        bus: LifecycleEventSink | None = LifecycleEventBus()
        if options and options.hook_sink:
            candidate = options.hook_sink
            if isinstance(candidate, LifecycleEventSink):
                bus = candidate
            elif hasattr(candidate, "emit") and hasattr(candidate, "drain"):
                bus = candidate  # best-effort duck typing
        hooks = _HookRelay(bus) if bus else None
        run_kwargs: dict[str, Any] = {}
        if options:
            if options.max_turns is not None:
                run_kwargs["max_turns"] = options.max_turns
            if options.previous_response_id:
                run_kwargs["previous_response_id"] = options.previous_response_id
            run_config = self._build_run_config(options)
            if run_config is not None:
                run_kwargs["run_config"] = run_config

        result = await Runner.run(
            agent,
            message,
            session=session,
            conversation_id=conversation_id,
            hooks=cast(RunHooksBase[Any, Agent[Any]] | None, hooks),
            **run_kwargs,
        )
        # Tests often mock Runner.run to return our domain AgentRunResult directly;
        # support both the SDK response shape and the domain model to keep the
        # runtime resilient to test doubles.
        if isinstance(result, AgentRunResult):
            usage = result.usage
            response_id = result.response_id
            final_output = result.final_output
            structured_output = result.structured_output
            response_text = result.response_text
            tool_outputs = result.tool_outputs
        else:
            context = getattr(result, "context_wrapper", None)
            usage = _convert_usage(getattr(context, "usage", None) if context else None)
            response_id = getattr(result, "last_response_id", None)
            final_output = getattr(result, "final_output", "")
            structured_output = None
            response_text = None
            tool_outputs = None
            if isinstance(final_output, str):
                response_text = final_output
            else:
                structured_output = final_output
                try:
                    response_text = json.dumps(final_output, ensure_ascii=False)
                except Exception:  # pragma: no cover - fallback serialization
                    response_text = str(final_output)
            raw_items = getattr(result, "new_items", None)
            if raw_items:
                mapped: list[Mapping[str, Any]] = []
                for item in raw_items:
                    mapping = AgentStreamEvent._to_mapping(item)
                    if mapping is not None:
                        mapped.append(mapping)
                tool_outputs = mapped or None
        base_metadata: dict[str, Any] = {"agent_key": agent_key, "model": str(agent.model)}
        metadata_payload: Mapping[str, Any]
        if safe_metadata:
            metadata_payload = {**base_metadata, **safe_metadata}
        else:
            metadata_payload = base_metadata
        return AgentRunResult(
            final_output=final_output,
            response_id=response_id,
            usage=usage,
            metadata=metadata_payload,
            structured_output=structured_output,
            response_text=response_text if response_text is not None else str(final_output),
            tool_outputs=tool_outputs,
        )

    def run_stream(
        self,
        agent_key: str,
        message: str,
        *,
        session: AgentSessionHandle | None = None,
        conversation_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        options: RunOptions | None = None,
    ) -> AgentStreamingHandle:
        runtime_ctx = None
        safe_metadata: dict[str, Any] = {}
        if isinstance(metadata, Mapping):
            runtime_ctx = metadata.get("prompt_runtime_ctx")
            safe_metadata = {k: v for k, v in metadata.items() if k != "prompt_runtime_ctx"}
        elif metadata is not None:
            logger.warning(
                "run_stream metadata ignored because it is not a mapping",
                extra={"type": type(metadata).__name__},
            )
        if runtime_ctx is None:
            runtime_ctx = self._bootstrap_ctx
        elif not isinstance(runtime_ctx, PromptRuntimeContext):
            raise TypeError("prompt_runtime_ctx must be a PromptRuntimeContext")
        agent = self._registry.get_agent_handle(
            agent_key,
            runtime_ctx=runtime_ctx,
            validate_prompts=True,
        )
        if agent is None:
            raise ValueError(f"Agent '{agent_key}' is not registered for OpenAI provider")
        bus: LifecycleEventSink | None = LifecycleEventBus()
        if options and options.hook_sink:
            candidate = options.hook_sink
            if isinstance(candidate, LifecycleEventSink):
                bus = candidate
            elif hasattr(candidate, "emit") and hasattr(candidate, "drain"):
                bus = candidate  # best-effort duck typing
        hooks = _HookRelay(bus) if bus else None

        run_kwargs: dict[str, Any] = {}
        if options:
            if options.max_turns is not None:
                run_kwargs["max_turns"] = options.max_turns
            if options.previous_response_id:
                run_kwargs["previous_response_id"] = options.previous_response_id
            run_config = self._build_run_config(options)
            if run_config is not None:
                run_kwargs["run_config"] = run_config

        stream = Runner.run_streamed(
            agent,
            message,
            session=session,
            conversation_id=conversation_id,
            hooks=cast(RunHooksBase[Any, Agent[Any]] | None, hooks),
            **run_kwargs,
        )
        base_metadata: dict[str, Any] = {"agent_key": agent_key, "model": str(agent.model)}
        metadata_payload = {**base_metadata, **safe_metadata}
        return OpenAIStreamingHandle(
            stream=stream,
            agent_key=agent_key,
            metadata=metadata_payload,
            lifecycle_bus=bus,
        )

    def _build_run_config(self, options: RunOptions | None) -> RunConfig | None:
        if not options:
            return None
        kwargs: dict[str, Any] = {}
        if options.handoff_input_filter:
            kwargs["handoff_input_filter"] = get_handoff_filter(options.handoff_input_filter)
        allowed = {
            "input_guardrails",
            "output_guardrails",
            "model",
            "model_settings",
            "tracing_disabled",
            "trace_include_sensitive_data",
            "workflow_name",
        }
        if options.run_config:
            for key, value in options.run_config.items():
                if key in allowed:
                    kwargs[key] = value
        if not kwargs:
            return None
        return RunConfig(**kwargs)


__all__ = ["OpenAIAgentRuntime", "OpenAIStreamingHandle"]
