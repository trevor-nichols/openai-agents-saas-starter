"""Agent registry and tool wiring for the OpenAI provider."""

from __future__ import annotations

import importlib
import logging
from collections.abc import Callable, Sequence
from datetime import datetime
from typing import Any, cast

from agents import Agent, CodeInterpreterTool, WebSearchTool, function_tool, handoff
from agents.agent_output import AgentOutputSchema, AgentOutputSchemaBase
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions

from app.agents._shared.handoff_filters import get_filter as get_handoff_filter
from app.agents._shared.loaders import (
    default_agent_key,
    resolve_prompt,
    topological_agent_order,
)
from app.agents._shared.prompt_context import (
    PromptRuntimeContext,
    build_prompt_context,
)
from app.agents._shared.prompt_template import render_prompt
from app.agents._shared.registry_loader import load_agent_specs
from app.agents._shared.specs import AgentSpec, HandoffConfig, OutputSpec
from app.core.settings import Settings
from app.domain.ai import AgentDescriptor
from app.services.agents.context import ConversationActorContext, get_current_actor
from app.utils.tools import ToolRegistry, initialize_tools
from openai.types.responses.tool_param import (
    CodeInterpreter,
    CodeInterpreterContainerCodeInterpreterToolAuto,
)

logger = logging.getLogger(__name__)
OPTIONAL_TOOL_KEYS: frozenset[str] = frozenset({"web_search"})


class OpenAIAgentRegistry:
    """Maintains concrete Agent instances and metadata."""

    def __init__(
        self,
        *,
        settings_factory: Callable[[], Settings],
        conversation_searcher,
        specs: Sequence[AgentSpec] | None = None,
    ) -> None:
        self._settings_factory = settings_factory
        self._conversation_searcher = conversation_searcher
        self._tool_registry: ToolRegistry = initialize_tools()
        self._agents: dict[str, Agent] = {}
        self._descriptors: dict[str, AgentDescriptor] = {}
        self._validated_static_agents: dict[str, Agent] | None = None
        self._specs: list[AgentSpec] = list(specs) if specs is not None else load_agent_specs()
        self._default_agent_key = default_agent_key(self._specs)
        self._static_ctx = PromptRuntimeContext(
            actor=ConversationActorContext(
                tenant_id="bootstrap-tenant",
                user_id="bootstrap-user",
            ),
            conversation_id="bootstrap",
            request_message="",
            settings=self._settings_factory(),
        )
        self._register_builtin_tools()
        # Build cached agents without strict validation; per-request rendering
        # runs with StrictUndefined using runtime context.
        self._build_agents_from_specs(
            runtime_ctx=self._static_ctx,
            validate_prompts=False,
            register_static=True,
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
    ) -> Agent | None:
        if runtime_ctx is None:
            if validate_prompts:
                if self._validated_static_agents is None:
                    self._validated_static_agents = self._build_agents_from_specs(
                        runtime_ctx=self._static_ctx,
                        validate_prompts=True,
                        register_static=False,
                    )
                return self._validated_static_agents.get(agent_key)
            return self._agents.get(agent_key)
        contextual_agents = self._build_agents_from_specs(
            runtime_ctx=runtime_ctx, validate_prompts=validate_prompts, register_static=False
        )
        return contextual_agents.get(agent_key)

    def get_descriptor(self, agent_key: str) -> AgentDescriptor | None:
        return self._descriptors.get(agent_key)

    def list_descriptors(self) -> Sequence[AgentDescriptor]:
        return [self._descriptors[name] for name in sorted(self._descriptors.keys())]

    def tool_overview(self) -> dict[str, Any]:
        return {
            "total_tools": len(self._tool_registry.list_tool_names()),
            "tool_names": self._tool_registry.list_tool_names(),
            "categories": self._tool_registry.list_categories(),
        }

    def resolve_agent(self, preferred_key: str | None) -> AgentDescriptor:
        key = preferred_key or self.default_agent_key
        descriptor = self.get_descriptor(key)
        if descriptor:
            return descriptor
        fallback = self.get_descriptor(self.default_agent_key)
        if not fallback:
            raise RuntimeError("No default agent configured for OpenAI provider.")
        return fallback

    def _build_agents_from_specs(
        self,
        *,
        runtime_ctx: PromptRuntimeContext | None,
        validate_prompts: bool,
        register_static: bool,
    ) -> dict[str, Agent]:
        settings = self._settings_factory()
        spec_map = {spec.key: spec for spec in self._specs}
        order = topological_agent_order(self._specs)

        agents: dict[str, Agent] = {}
        for key in order:
            spec = spec_map[key]
            agent = self._build_agent(
                spec=spec,
                settings=settings,
                runtime_ctx=runtime_ctx,
                agents=agents,
                validate_prompts=validate_prompts,
            )
            if register_static:
                self._register_agent(spec, agent)
            agents[key] = agent

        return agents

    def _build_agent(
        self,
        *,
        spec: AgentSpec,
        settings: Settings,
        runtime_ctx: PromptRuntimeContext | None,
        agents: dict[str, Agent],
        validate_prompts: bool,
    ) -> Agent:
        tools = self._select_tools(spec, runtime_ctx=runtime_ctx)
        raw_prompt = resolve_prompt(spec)
        prompt_ctx = (
            {} if runtime_ctx is None else self._build_prompt_context(spec, runtime_ctx=runtime_ctx)
        )
        instructions = render_prompt(
            raw_prompt,
            context=prompt_ctx,
            validate=validate_prompts,
        )
        if spec.wrap_with_handoff_prompt and spec.handoff_keys:
            instructions = prompt_with_handoff_instructions(instructions)

        handoff_targets = []
        for target in spec.handoff_keys:
            target_agent = agents.get(target) or self._agents.get(target)
            if target_agent is None:
                raise ValueError(
                    f"Agent '{spec.key}' declares handoff to '{target}' which is not loaded"
                )
            policy = getattr(spec, "handoff_context", {}).get(target, "full")
            override = getattr(spec, "handoff_overrides", {}).get(target, None)
            input_filter = self._resolve_handoff_filter(policy=policy, override=override)
            input_type = self._resolve_input_type(override)
            tool_name = override.tool_name if isinstance(override, HandoffConfig) else None
            tool_desc = override.tool_description if isinstance(override, HandoffConfig) else None
            is_enabled = (
                override.is_enabled
                if isinstance(override, HandoffConfig) and override.is_enabled is not None
                else True
            )

            kwargs: dict[str, Any] = {
                "input_filter": input_filter,
                "tool_name_override": tool_name,
                "tool_description_override": tool_desc,
                "is_enabled": is_enabled,
            }
            if input_type is not None:
                kwargs["input_type"] = input_type
            handoff_targets.append(handoff(target_agent, **kwargs))

        return Agent(
            name=spec.display_name,
            instructions=instructions,
            model=self._resolve_agent_model(settings, spec),
            tools=tools,
            handoffs=cast(list[Any], handoff_targets),
            handoff_description=spec.description if handoff_targets else None,
            output_type=self._resolve_output_type(spec),
        )

    def _register_agent(self, spec: AgentSpec, agent: Agent) -> None:
        self._agents[spec.key] = agent
        self._descriptors[spec.key] = AgentDescriptor(
            key=spec.key,
            display_name=spec.display_name,
            description=spec.description.strip(),
            model=str(agent.model),
            capabilities=spec.capabilities,
        )

    def _select_tools(
        self, spec: AgentSpec, *, runtime_ctx: PromptRuntimeContext | None
    ) -> list[Any]:
        settings = self._settings_factory()
        tool_keys = getattr(spec, "tool_keys", ()) or ()
        tools: list[Any] = []
        missing_required: list[str] = []
        missing_optional: list[str] = []
        tool_configs = getattr(spec, "tool_configs", {}) or {}
        for name in tool_keys:
            tool = self._tool_registry.get_tool(name)
            if tool is None:
                if name in OPTIONAL_TOOL_KEYS:
                    missing_optional.append(name)
                else:
                    missing_required.append(name)
                continue
            # Code Interpreter special handling (auto vs explicit)
            if isinstance(tool, CodeInterpreterTool):
                config = tool_configs.get("code_interpreter", {})
                mode = config.get("mode", "auto")
                memory_limit = config.get("memory_limit") or settings.container_default_auto_memory
                file_ids = config.get("file_ids")
                container_id: str | None = None
                if runtime_ctx and runtime_ctx.container_bindings:
                    container_id = runtime_ctx.container_bindings.get(spec.key)
                if config.get("container_id"):
                    container_id = config.get("container_id")

                if mode == "explicit" and not container_id:
                    if not settings.container_fallback_to_auto_on_missing_binding:
                        raise ValueError(
                            f"Agent '{spec.key}' requires explicit code interpreter container "
                            "but none is bound"
                        )
                if container_id:
                    tool_config: CodeInterpreter = cast(
                        CodeInterpreter,
                        {"type": "code_interpreter", "container": container_id},
                    )
                    tools.append(CodeInterpreterTool(tool_config=tool_config))
                else:
                    auto_container = cast(
                        CodeInterpreterContainerCodeInterpreterToolAuto,
                        {"type": "auto", "memory_limit": memory_limit},
                    )
                    if file_ids:
                        auto_container = cast(
                            CodeInterpreterContainerCodeInterpreterToolAuto,
                            {"type": "auto", "memory_limit": memory_limit, "file_ids": file_ids},
                        )
                    tool_config = cast(
                        CodeInterpreter,
                        {"type": "code_interpreter", "container": auto_container},
                    )
                    tools.append(CodeInterpreterTool(tool_config=tool_config))
            else:
                tools.append(tool)
        if missing_required:
            raise ValueError(
                f"Agent '{spec.key}' declares tool_keys {tool_keys} but these tools are "
                f"not registered: {', '.join(missing_required)}"
            )
        if missing_optional:
            logger.warning(
                "tools.missing_optional_for_agent",
                extra={"agent": spec.key, "missing_tools": missing_optional},
            )

        # Clone hosted web search tool with request-scoped location, if provided.
        if runtime_ctx and runtime_ctx.user_location:
            customized: list[Any] = []
            for tool in tools:
                if isinstance(tool, WebSearchTool):
                    customized.append(
                        WebSearchTool(
                            user_location=runtime_ctx.user_location,
                            filters=tool.filters,
                            search_context_size=tool.search_context_size,
                        )
                    )
                else:
                    customized.append(tool)
            return customized

        return tools

    def _register_builtin_tools(self) -> None:
        """Register internal utility tools; agents opt in via tool_keys."""

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

    def _build_prompt_context(
        self, spec: AgentSpec, *, runtime_ctx: PromptRuntimeContext
    ) -> dict[str, Any]:
        return build_prompt_context(spec=spec, runtime_ctx=runtime_ctx, base=None)

    def _resolve_agent_model(self, settings: Settings, spec: AgentSpec) -> str:
        if spec.model_key:
            attr = f"agent_{spec.model_key}_model"
            override = getattr(settings, attr, None)
            if override:
                return override
        return settings.agent_default_model

    def _resolve_handoff_filter(
        self, *, policy: str, override: HandoffConfig | None
    ):
        """Return an SDK handoff input_filter based on policy or override name."""

        # Override takes precedence
        if override and override.input_filter:
            return get_handoff_filter(override.input_filter)

        return get_handoff_filter(policy)

    def _resolve_input_type(self, override: HandoffConfig | None):
        """Resolve dotted-path input type to a Python class if provided."""

        if not override or not override.input_type:
            return None
        return self._import_object(override.input_type, expected=None)

    def _resolve_output_type(self, spec: AgentSpec) -> AgentOutputSchemaBase | type[Any] | None:
        cfg: OutputSpec | None = getattr(spec, "output", None)
        if cfg is None or cfg.mode == "text":
            return None

        # Custom schema overrides all.
        if cfg.custom_schema_path:
            schema_obj = self._import_object(
                cfg.custom_schema_path, expected=AgentOutputSchemaBase, label="custom_schema_path"
            )
            if isinstance(schema_obj, type) and issubclass(schema_obj, AgentOutputSchemaBase):
                return schema_obj()
            if isinstance(schema_obj, AgentOutputSchemaBase):
                return schema_obj
            raise ValueError(
                f"custom_schema_path '{cfg.custom_schema_path}' must resolve to "
                "AgentOutputSchemaBase or subclass"
            )

        if not cfg.type_path:
            raise ValueError(
                f"Agent '{spec.key}' output.mode=json_schema requires 'type_path' to be set"
            )

        type_obj = self._import_object(cfg.type_path, expected=None, label="type_path")
        return AgentOutputSchema(type_obj, strict_json_schema=cfg.strict)

    # Backwards-compatible helper used in tests.
    def _make_handoff_input_filter(self, policy: str):
        return self._resolve_handoff_filter(policy=policy, override=None)

    @staticmethod
    def _import_object(path: str, expected: type[Any] | None = None, label: str | None = None):
        """Import an object from dotted path with optional type check."""

        dotted = path
        if ":" in dotted:
            module_path, attr = dotted.split(":", 1)
        elif "." in dotted:
            module_path, attr = dotted.rsplit(".", 1)
        else:
            raise ValueError(f"Invalid dotted path '{dotted}'")

        module = importlib.import_module(module_path)
        obj = getattr(module, attr, None)
        if obj is None:
            raise ValueError(f"{label or 'object'} '{dotted}' could not be resolved")
        if expected and not isinstance(obj, expected):
            # Allow passing classes when expected is a baseclass type
            if not (isinstance(expected, type) and issubclass(obj, expected)):
                raise ValueError(
                    f"{label or 'object'} '{dotted}' must be an instance of {expected.__name__}"
                )
        return obj


__all__ = ["OpenAIAgentRegistry"]
