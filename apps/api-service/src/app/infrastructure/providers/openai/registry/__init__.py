"""OpenAI agent registry orchestration.

This package breaks the legacy monolith into focused collaborators:
- ToolResolver: resolves declarative tool keys.
- PromptRenderer: builds and renders prompts.
- AgentBuilder: constructs concrete SDK Agents.
- DescriptorStore: tracks descriptors and visibility metadata.
- GuardrailBuilder: constructs SDK guardrails from specs (optional).
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Any

from agents import Agent, function_tool

from app.agents._shared.loaders import default_agent_key, topological_agent_order
from app.agents._shared.prompt_context import PromptRuntimeContext
from app.agents._shared.registry_loader import load_agent_specs
from app.agents._shared.specs import AgentSpec
from app.core.settings import Settings
from app.domain.ai import AgentDescriptor, StreamEventBus
from app.services.agents.context import get_current_actor
from app.utils.tools import ToolRegistry, initialize_tools

from .agent_builder import AgentBuilder
from .descriptors import DescriptorStore
from .prompt import PromptRenderer
from .tool_resolver import ToolResolver

if TYPE_CHECKING:
    from app.guardrails._shared.builder import GuardrailBuilder
    from app.guardrails._shared.registry import GuardrailRegistry

logger = logging.getLogger(__name__)


class OpenAIAgentRegistry:
    """Maintains concrete Agent instances and metadata."""

    def __init__(
        self,
        *,
        settings_factory: Callable[[], Settings],
        conversation_searcher,
        specs: Sequence[AgentSpec] | None = None,
        tool_registry: ToolRegistry | None = None,
        guardrail_registry: GuardrailRegistry | None = None,
        default_guardrails: Any | None = None,
        default_guardrail_runtime: Any | None = None,
        default_tool_guardrails: Any | None = None,
    ) -> None:
        self._settings_factory = settings_factory
        self._conversation_searcher = conversation_searcher
        self._tool_registry: ToolRegistry = tool_registry or initialize_tools()
        self._prompt_renderer = PromptRenderer(settings_factory=settings_factory)

        # Build guardrails lazily if registry provided
        guardrail_builder: GuardrailBuilder | None = None
        if guardrail_registry is not None:
            from app.guardrails._shared.builder import GuardrailBuilder as GB

            guardrail_builder = GB(guardrail_registry)
            logger.debug("GuardrailBuilder initialized with registry")

        self._tool_resolver = ToolResolver(
            tool_registry=self._tool_registry,
            settings_factory=settings_factory,
            guardrail_builder=guardrail_builder,
            default_tool_guardrails=default_tool_guardrails,
        )

        self._agent_builder = AgentBuilder(
            tool_resolver=self._tool_resolver,
            prompt_renderer=self._prompt_renderer,
            settings_factory=settings_factory,
            guardrail_builder=guardrail_builder,
            default_guardrails=default_guardrails,
            default_runtime_options=default_guardrail_runtime,
        )
        self._descriptors = DescriptorStore()

        self._agents: dict[str, Agent] = {}
        self._validated_static_agents: dict[str, Agent] | None = None
        if specs is not None:
            self._specs = list(specs)
        else:
            self._specs = load_agent_specs()
        self._default_agent_key = default_agent_key(self._specs)
        self._code_interpreter_modes: dict[str, str] = {}
        self._agent_tool_names: dict[str, list[str]] = {}
        self._static_ctx = self._prompt_renderer.build_static_context()

        self._register_builtin_tools()
        self._build_agents_from_specs(
            runtime_ctx=self._static_ctx,
            validate_prompts=False,
            register_static=True,
            allow_unresolved_file_search=True,
        )

    @property
    def default_agent_key(self) -> str:
        return self._default_agent_key

    def get_agent_handle(
        self,
        agent_key: str,
        *,
        runtime_ctx: PromptRuntimeContext | None = None,
        validate_prompts: bool = True,
        tool_stream_bus: StreamEventBus | None = None,
    ) -> Agent | None:
        if runtime_ctx is None:
            if validate_prompts:
                if self._validated_static_agents is None:
                    self._validated_static_agents = self._build_agents_from_specs(
                        runtime_ctx=self._static_ctx,
                        validate_prompts=True,
                        register_static=False,
                        allow_unresolved_file_search=True,
                        tool_stream_bus=None,
                    )
                return self._validated_static_agents.get(agent_key)
            return self._agents.get(agent_key)

        contextual_agents = self._build_agents_from_specs(
            runtime_ctx=runtime_ctx,
            validate_prompts=validate_prompts,
            register_static=False,
            allow_unresolved_file_search=runtime_ctx.file_search is None,
            tool_stream_bus=tool_stream_bus,
        )
        return contextual_agents.get(agent_key)

    def get_descriptor(self, agent_key: str) -> AgentDescriptor | None:
        return self._descriptors.get(agent_key)

    def get_code_interpreter_mode(self, agent_key: str) -> str | None:
        return self._code_interpreter_modes.get(agent_key)

    def get_agent_tool_names(self, agent_key: str) -> list[str]:
        return list(self._agent_tool_names.get(agent_key, []))

    def list_descriptors(self) -> Sequence[AgentDescriptor]:
        return self._descriptors.list()

    def tool_overview(self) -> dict[str, Any]:
        return {
            "total_tools": len(self._tool_registry.list_tool_names()),
            "tool_names": self._tool_registry.list_tool_names(),
            "categories": self._tool_registry.list_categories(),
            "per_agent": self._tools_by_agent(),
        }

    def mark_seen(self, agent_key: str, ts: datetime) -> None:
        self._descriptors.mark_seen(agent_key, ts)

    def resolve_agent(self, preferred_key: str | None) -> AgentDescriptor:
        key = preferred_key or self.default_agent_key
        descriptor = self.get_descriptor(key)
        if descriptor:
            return descriptor
        fallback = self.get_descriptor(self.default_agent_key)
        if not fallback:
            raise RuntimeError("No default agent configured for OpenAI provider.")
        return fallback

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_agents_from_specs(
        self,
        *,
        runtime_ctx: PromptRuntimeContext | None,
        validate_prompts: bool,
        register_static: bool,
        allow_unresolved_file_search: bool = False,
        tool_stream_bus: StreamEventBus | None = None,
    ) -> dict[str, Agent]:
        spec_map = {spec.key: spec for spec in self._specs}
        order = topological_agent_order(self._specs)

        agents: dict[str, Agent] = {}
        for key in order:
            spec = spec_map[key]
            build_result = self._agent_builder.build_agent(
                spec=spec,
                runtime_ctx=runtime_ctx,
                agents=agents,
                spec_map=spec_map,
                validate_prompts=validate_prompts,
                allow_unresolved_file_search=allow_unresolved_file_search,
                static_agents=self._agents,
                tool_stream_bus=tool_stream_bus,
            )
            if build_result.code_interpreter_mode:
                self._code_interpreter_modes[spec.key] = build_result.code_interpreter_mode
            if build_result.agent_tool_names:
                self._agent_tool_names[spec.key] = list(build_result.agent_tool_names)
            if register_static:
                self._register_agent(spec, build_result.agent)
            agents[key] = build_result.agent

        return agents

    def _register_agent(self, spec: AgentSpec, agent: Agent) -> None:
        self._agents[spec.key] = agent
        self._descriptors.register(spec, agent)

    def _tools_by_agent(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for spec in self._specs:
            tool_keys = list(getattr(spec, "tool_keys", []) or [])
            agent_tool_keys = list(getattr(spec, "agent_tool_keys", []) or [])
            combined = tool_keys + agent_tool_keys
            result[spec.key] = combined
        return result

    # Legacy helpers kept for tests/backward compatibility -----------------
    def _build_agent_tools(
        self,
        *,
        spec: AgentSpec,
        spec_map: dict[str, AgentSpec],
        agents: dict[str, Agent],
        tools: list[Any],
    ) -> list[Any]:
        return self._agent_builder._build_agent_tools(
            spec=spec,
            spec_map=spec_map,
            agents=agents,
            tools=tools,
            static_agents=self._agents,
        )

    def _make_handoff_input_filter(self, policy: str):
        # Backwards-compatible helper used in tests.
        return self._agent_builder._resolve_handoff_filter(
            policy=policy, override=None
        )

    # Built-in utility tools ------------------------------------------------
    def _register_builtin_tools(self) -> None:
        self._tool_registry.register_tool(
            self._build_current_time_tool(),
            category="utility",
            metadata={"description": "Return the current UTC timestamp."},
        )
        self._tool_registry.register_tool(
            self._build_conversation_search_tool(),
            category="conversation",
            metadata={"description": "Search cached conversation history."},
        )

    def _build_current_time_tool(self):
        @function_tool
        async def get_current_time() -> str:
            return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        return get_current_time

    def _build_conversation_search_tool(self):
        conversation_searcher = self._conversation_searcher

        @function_tool
        async def search_conversations(query: str) -> str:
            actor = get_current_actor()
            if actor is None:
                return "Conversation search is unavailable until tenant context is established."
            results = await conversation_searcher(tenant_id=actor.tenant_id, query=query)
            if hasattr(results, "items"):
                results = results.items
            if not results:
                return "No conversations contained the requested text."
            top_matches = "\n".join(
                f"{result.conversation_id}: {result.preview}" for result in results[:5]
            )
            return f"Found {len(results)} matching conversations:\n{top_matches}"

        return search_conversations


__all__ = ["OpenAIAgentRegistry"]
