"""Agent construction separated from registry orchestration."""

from __future__ import annotations

import importlib
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from agents import Agent, RunConfig, handoff
from agents.agent_output import AgentOutputSchema, AgentOutputSchemaBase
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from agents.model_settings import ModelSettings

from app.agents._shared.handoff_filters import get_filter as get_handoff_filter
from app.agents._shared.specs import (
    AgentSpec,
    AgentToolConfig,
    GuardrailRuntimeOptions,
    HandoffConfig,
    OutputSpec,
)
from app.core.settings import Settings

from .prompt import PromptRenderer
from .tool_resolver import ToolResolver

if TYPE_CHECKING:
    from app.guardrails._shared.builder import GuardrailBuilder

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class BuildResult:
    agent: Agent
    code_interpreter_mode: str | None


class AgentBuilder:
    def __init__(
        self,
        *,
        tool_resolver: ToolResolver,
        prompt_renderer: PromptRenderer,
        settings_factory: Callable[[], Settings],
        guardrail_builder: GuardrailBuilder | None = None,
        default_guardrails: Any | None = None,
        default_runtime_options: GuardrailRuntimeOptions | None = None,
    ) -> None:
        self._tool_resolver = tool_resolver
        self._prompt_renderer = prompt_renderer
        self._settings_factory = settings_factory
        self._guardrail_builder = guardrail_builder
        self._default_guardrails = default_guardrails
        self._default_runtime_options = default_runtime_options

    def build_agent(
        self,
        *,
        spec: AgentSpec,
        runtime_ctx,
        agents: dict[str, Agent],
        spec_map: dict[str, AgentSpec],
        validate_prompts: bool,
        allow_unresolved_file_search: bool = False,
        static_agents: dict[str, Agent] | None = None,
    ) -> BuildResult:
        tool_selection = self._tool_resolver.select_tools(
            spec,
            runtime_ctx=runtime_ctx,
            allow_unresolved_file_search=allow_unresolved_file_search,
        )
        spec.ensure_model_config()
        instructions, _ = self._prompt_renderer.render_instructions(
            spec=spec,
            runtime_ctx=runtime_ctx,
            validate_prompts=validate_prompts,
        )
        if spec.wrap_with_handoff_prompt and spec.handoff_keys:
            instructions = prompt_with_handoff_instructions(instructions)

        handoff_targets = self._build_handoffs(spec, agents, static_agents=static_agents)
        agent_tools = self._build_agent_tools(
            spec=spec,
            spec_map=spec_map,
            agents=agents,
            tools=tool_selection.tools,
            static_agents=static_agents,
        )

        tools_with_agents = tool_selection.tools + agent_tools

        response_include: list[str] = []
        if "code_interpreter" in getattr(spec, "tool_keys", ()):  # maintain order guard
            response_include.append("code_interpreter_call.outputs")
        model_settings = ModelSettings(response_include=response_include or None)

        # Build guardrails if configured
        input_guardrails, output_guardrails = self._build_guardrails(spec)

        # Build agent kwargs with optional guardrails
        agent_kwargs: dict[str, Any] = {
            "name": spec.display_name,
            "instructions": instructions,
            "model": self._resolve_agent_model(self._settings_factory(), spec),
            "model_settings": model_settings,
            "tools": tools_with_agents,
            "handoffs": cast(list[Any], handoff_targets),
            "handoff_description": spec.description if handoff_targets else None,
            "output_type": self._resolve_output_type(spec),
        }
        if input_guardrails:
            agent_kwargs["input_guardrails"] = input_guardrails
        if output_guardrails:
            agent_kwargs["output_guardrails"] = output_guardrails
        runtime_opts = spec.guardrails_runtime or self._default_runtime_options
        if runtime_opts:
            agent_kwargs.setdefault("guardrails_runtime", self._runtime_options(runtime_opts))

        agent = Agent(**agent_kwargs)
        return BuildResult(agent=agent, code_interpreter_mode=tool_selection.code_interpreter_mode)

    def _build_agent_tools(
        self,
        *,
        spec: AgentSpec,
        spec_map: dict[str, AgentSpec],
        agents: dict[str, Agent],
        tools: list[Any],
        static_agents: dict[str, Agent] | None = None,
    ) -> list[Any]:
        if not getattr(spec, "agent_tool_keys", None):
            return []

        existing_names = {getattr(t, "name", None) for t in tools if hasattr(t, "name")}
        results: list[Any] = []

        for agent_key in spec.agent_tool_keys:
            target_agent = agents.get(agent_key) or (static_agents or {}).get(agent_key)
            if target_agent is None:
                raise ValueError(
                    f"Agent '{spec.key}' declares agent_tool '{agent_key}' which is not loaded"
                )

            override: AgentToolConfig | None = getattr(spec, "agent_tool_overrides", {}).get(
                agent_key
            )

            tool_name = override.tool_name if isinstance(override, AgentToolConfig) else None
            tool_description = (
                override.tool_description if isinstance(override, AgentToolConfig) else None
            )
            custom_output_extractor = None
            is_enabled: bool | None = None
            run_config: RunConfig | None = None
            max_turns: int | None = None

            if isinstance(override, AgentToolConfig):
                if override.custom_output_extractor:
                    custom_output_extractor = self._import_object(
                        override.custom_output_extractor,
                        expected=None,
                        label="custom_output_extractor",
                    )
                if override.is_enabled is not None:
                    if isinstance(override.is_enabled, bool):
                        is_enabled = override.is_enabled
                    elif isinstance(override.is_enabled, str):
                        is_enabled = self._import_object(
                            override.is_enabled,
                            expected=None,
                            label="agent_tool_is_enabled",
                        )
                    else:
                        raise ValueError(
                            "agent_tool_overrides.is_enabled must be bool or dotted path"
                        )
                if override.run_config is not None:
                    if isinstance(override.run_config, RunConfig):
                        run_config = override.run_config
                    elif isinstance(override.run_config, dict):
                        run_config = RunConfig(**override.run_config)
                    else:
                        raise ValueError(
                            "agent_tool_overrides.run_config for "
                            f"'{agent_key}' must be dict or RunConfig"
                        )
                if override.max_turns is not None:
                    max_turns = override.max_turns

            spec_entry = spec_map.get(agent_key)
            spec_desc = spec_entry.description if spec_entry else None
            desc_fallback = (
                tool_description
                or target_agent.handoff_description
                or spec_desc
                or f"Wrapped agent '{agent_key}'"
            )

            final_name = tool_name or target_agent.name
            if final_name in existing_names:
                raise ValueError(
                    f"Agent '{spec.key}' tried to register agent-tool "
                    f"'{final_name}' but that name already exists"
                )
            existing_names.add(final_name)

            results.append(
                target_agent.as_tool(
                    tool_name=final_name,
                    tool_description=desc_fallback,
                    custom_output_extractor=custom_output_extractor,
                    is_enabled=is_enabled if is_enabled is not None else True,
                    run_config=run_config,
                    max_turns=max_turns,
                )
            )

        return results

    def _build_handoffs(
        self,
        spec: AgentSpec,
        agents: dict[str, Agent],
        static_agents: dict[str, Agent] | None = None,
    ):
        handoff_targets = []
        for target in spec.handoff_keys:
            target_agent = agents.get(target) or (static_agents or {}).get(target)
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
        return handoff_targets

    @staticmethod
    def _resolve_handoff_filter(*, policy: str, override: HandoffConfig | None):
        if override and override.input_filter:
            return get_handoff_filter(override.input_filter)
        return get_handoff_filter(policy)

    @staticmethod
    def _resolve_input_type(override: HandoffConfig | None):
        if not override or not override.input_type:
            return None
        return AgentBuilder._import_object(override.input_type, expected=None)

    def _resolve_output_type(self, spec: AgentSpec) -> AgentOutputSchemaBase | type[Any] | None:
        cfg: OutputSpec | None = getattr(spec, "output", None)
        if cfg is None or cfg.mode == "text":
            return None

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

    def _resolve_agent_model(self, settings: Settings, spec: AgentSpec) -> str:
        if spec.model is not None:
            return str(spec.model)
        if spec.model_key:
            attr = f"agent_{spec.model_key}_model"
            override = getattr(settings, attr, None)
            if override:
                return override
        return settings.agent_default_model

    @staticmethod
    def _import_object(path: str, expected: type[Any] | None = None, label: str | None = None):
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
            if not (isinstance(expected, type) and issubclass(obj, expected)):
                raise ValueError(
                    f"{label or 'object'} '{dotted}' must be an instance of {expected.__name__}"
                )
        return obj

    def _build_guardrails(
        self,
        spec: AgentSpec,
    ) -> tuple[list[Any], list[Any]]:
        """Build input and output guardrails from agent spec.

        Args:
            spec: The agent specification.

        Returns:
            Tuple of (input_guardrails, output_guardrails) lists.
        """
        guardrail_config = getattr(spec, "guardrails", None) or self._default_guardrails
        if guardrail_config is None or not self._guardrail_builder:
            return [], []

        try:
            input_guardrails = self._guardrail_builder.build_input_guardrails(guardrail_config)
            output_guardrails = self._guardrail_builder.build_output_guardrails(guardrail_config)
            logger.debug(
                "Built guardrails for agent '%s': %d input, %d output",
                spec.key,
                len(input_guardrails),
                len(output_guardrails),
            )
            return input_guardrails, output_guardrails
        except Exception as e:
            logger.exception("Failed to build guardrails for agent '%s': %s", spec.key, e)
            raise ValueError(
                f"Failed to build guardrails for agent '{spec.key}': {e}"
            ) from e

    @staticmethod
    def _runtime_options(
        options: GuardrailRuntimeOptions,
    ) -> dict[str, Any]:
        """Translate GuardrailRuntimeOptions to Agent kwargs."""
        runtime: dict[str, Any] = {
            "suppress_tripwire": options.suppress_tripwire,
            "streaming_mode": options.streaming_mode,
        }
        if options.concurrency is not None:
            runtime["concurrency"] = options.concurrency
        if options.result_handler_path:
            runtime["result_handler_path"] = options.result_handler_path
        return runtime


__all__ = ["AgentBuilder", "BuildResult"]
