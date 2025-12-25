"""OpenAI Agents SDK runtime adapters implementing domain ports."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from typing import Any, cast

from agents import Agent, Runner
from agents.lifecycle import RunHooksBase

from app.agents._shared.prompt_context import PromptRuntimeContext
from app.core.settings import get_settings
from app.domain.ai import AgentRunResult, RunOptions, StreamEventBus
from app.domain.ai.models import AgentStreamEvent
from app.domain.ai.ports import (
    AgentInput,
    AgentRuntime,
    AgentSessionHandle,
    AgentStreamingHandle,
)
from app.services.agents.context import ConversationActorContext

from .context import resolve_runtime_context
from .lifecycle import HookRelay, LifecycleEventBus, LifecycleEventSink
from .run_config import build_run_config
from .streaming import OpenAIStreamingHandle
from .usage import convert_usage

logger = logging.getLogger(__name__)


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
            file_search=None,
            client_overrides=None,
            container_bindings=None,
        )

    async def run(
        self,
        agent_key: str,
        message: AgentInput,
        *,
        session: AgentSessionHandle | None = None,
        conversation_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        options: RunOptions | None = None,
    ) -> AgentRunResult:
        agent, safe_metadata, hooks, bus = self._prepare_run(
            agent_key,
            metadata=metadata,
            options=options,
        )
        run_kwargs = self._prepare_run_kwargs(options)

        handoff_count = 0
        final_agent: str | None = agent_key

        input_payload = cast(Any, message)
        result = await Runner.run(
            agent,
            input_payload,
            session=session,
            conversation_id=conversation_id,
            hooks=cast(RunHooksBase[Any, Agent[Any]] | None, hooks),
            **run_kwargs,
        )

        if bus is not None:
            async for ev in bus.drain():
                if getattr(ev, "event", None) == "handoff":
                    handoff_count += 1
                    if getattr(ev, "new_agent", None):
                        final_agent = ev.new_agent

        # When upstream already returns an AgentRunResult (e.g., tests or alternate
        # runtimes), respect its handoff metadata instead of re-deriving it from
        # lifecycle events.
        if isinstance(result, AgentRunResult):
            if result.final_agent is not None:
                final_agent = result.final_agent
            if result.handoff_count is not None:
                handoff_count = result.handoff_count

        usage, response_id, final_output, structured_output, response_text, tool_outputs = (
            self._normalize_run_result(result)
        )
        metadata_payload = self._build_metadata(agent_key, agent.model, safe_metadata)

        return AgentRunResult(
            final_output=final_output,
            response_id=response_id,
            usage=usage,
            metadata=metadata_payload,
            structured_output=structured_output,
            response_text=response_text if response_text is not None else str(final_output),
            tool_outputs=tool_outputs,
            handoff_count=handoff_count or None,
            final_agent=final_agent,
        )

    def run_stream(
        self,
        agent_key: str,
        message: AgentInput,
        *,
        session: AgentSessionHandle | None = None,
        conversation_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        options: RunOptions | None = None,
    ) -> AgentStreamingHandle:
        tool_stream_bus = StreamEventBus()
        agent, safe_metadata, hooks, bus = self._prepare_run(
            agent_key,
            metadata=metadata,
            options=options,
            tool_stream_bus=tool_stream_bus,
        )
        run_kwargs = self._prepare_run_kwargs(options)

        input_payload = cast(Any, message)
        stream = Runner.run_streamed(
            agent,
            input_payload,
            session=session,
            conversation_id=conversation_id,
            hooks=cast(RunHooksBase[Any, Agent[Any]] | None, hooks),
            **run_kwargs,
        )

        metadata_payload = self._build_metadata(agent_key, agent.model, safe_metadata)
        return OpenAIStreamingHandle(
            stream=stream,
            agent_key=agent_key,
            metadata=metadata_payload,
            lifecycle_bus=bus,
            tool_stream_bus=tool_stream_bus,
        )

    # internal helpers -----------------------------------------------------

    def _prepare_run(
        self,
        agent_key: str,
        *,
        metadata: Mapping[str, Any] | None,
        options: RunOptions | None,
        tool_stream_bus: StreamEventBus | None = None,
    ) -> tuple[Agent, dict[str, Any], HookRelay | None, LifecycleEventSink | None]:
        runtime_ctx, safe_metadata = resolve_runtime_context(
            metadata,
            bootstrap_ctx=self._bootstrap_ctx,
        )
        agent = self._registry.get_agent_handle(
            agent_key,
            runtime_ctx=runtime_ctx,
            validate_prompts=True,
            tool_stream_bus=tool_stream_bus,
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
        hooks = HookRelay(bus) if bus else None
        return agent, safe_metadata, hooks, bus

    def _prepare_run_kwargs(self, options: RunOptions | None) -> dict[str, Any]:
        run_kwargs: dict[str, Any] = {}
        if not options:
            return run_kwargs
        if options.max_turns is not None:
            run_kwargs["max_turns"] = options.max_turns
        if options.previous_response_id:
            run_kwargs["previous_response_id"] = options.previous_response_id
        run_config = build_run_config(options)
        if run_config is not None:
            run_kwargs["run_config"] = run_config
        return run_kwargs

    def _normalize_run_result(self, result) -> tuple[Any, Any, Any, Any, Any, Any]:
        if isinstance(result, AgentRunResult):
            return (
                result.usage,
                result.response_id,
                result.final_output,
                result.structured_output,
                result.response_text,
                result.tool_outputs,
            )

        context = getattr(result, "context_wrapper", None)
        usage = convert_usage(getattr(context, "usage", None) if context else None)
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
            mapped = [
                AgentStreamEvent._to_mapping(item)
                for item in raw_items
                if AgentStreamEvent._to_mapping(item) is not None
            ]
            tool_outputs = mapped or None

        return usage, response_id, final_output, structured_output, response_text, tool_outputs

    def _build_metadata(
        self, agent_key: str, model: Any, safe_metadata: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        base_metadata: dict[str, Any] = {"agent_key": agent_key, "model": str(model)}
        mode = self._registry.get_code_interpreter_mode(agent_key)
        if mode:
            base_metadata["code_interpreter_mode"] = mode
        agent_tool_names = self._registry.get_agent_tool_names(agent_key)
        if agent_tool_names:
            base_metadata["agent_tool_names"] = agent_tool_names
        if safe_metadata:
            return {**base_metadata, **safe_metadata}
        return base_metadata


__all__ = ["OpenAIAgentRuntime", "OpenAIStreamingHandle"]
