"""Constructs SDK-compatible guardrail functions from specifications.

This module provides the `GuardrailBuilder` class that transforms declarative
`GuardrailSpec` instances into concrete guardrail functions compatible with
the OpenAI Agents SDK.

Architecture follows the same pattern as `AgentBuilder` in
`app.infrastructure.providers.openai.registry.agent_builder`.
"""

from __future__ import annotations

import importlib
import logging
from typing import TYPE_CHECKING, Any

from agents import InputGuardrail, OutputGuardrail
from agents.guardrail import GuardrailFunctionOutput
from agents.tool_guardrails import (
    AllowBehavior,
    RaiseExceptionBehavior,
    ToolGuardrailFunctionOutput,
    ToolInputGuardrail,
    ToolInputGuardrailData,
    ToolOutputGuardrail,
    ToolOutputGuardrailData,
)

from app.guardrails._shared.specs import (
    AgentGuardrailConfig,
    GuardrailCheckResult,
    GuardrailSpec,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from app.guardrails._shared.registry import GuardrailRegistry

    # Type for check functions
    CheckFn = Callable[..., Awaitable[GuardrailCheckResult]]

logger = logging.getLogger(__name__)


class GuardrailBuilder:
    """Builds SDK guardrail functions from declarative specs.

    This builder transforms `GuardrailSpec` instances into `InputGuardrail`
    and `OutputGuardrail` instances that can be attached to SDK `Agent` objects.

    The builder:
    1. Resolves guardrails from presets and explicit configs
    2. Imports check functions from dotted paths
    3. Creates wrapper functions that match SDK expectations
    4. Returns SDK guardrail objects

    Usage:
        builder = GuardrailBuilder(registry)
        input_guardrails = builder.build_input_guardrails(config)
        output_guardrails = builder.build_output_guardrails(config)
    """

    def __init__(self, registry: GuardrailRegistry) -> None:
        """Initialize the builder.

        Args:
            registry: The guardrail registry containing specs and presets.
        """
        self._registry = registry
        self._check_fn_cache: dict[str, CheckFn] = {}

    def build_input_guardrails(
        self,
        config: AgentGuardrailConfig,
    ) -> list[InputGuardrail[Any]]:
        """Build input guardrails for an agent.

        Creates SDK InputGuardrail instances for guardrails configured to
        run at pre_flight or input stages.

        Args:
            config: The agent's guardrail configuration.

        Returns:
            List of InputGuardrail instances.
        """
        resolved = self._resolve_guardrails(config)
        guardrails: list[InputGuardrail[Any]] = []

        for spec, cfg in resolved:
            if spec.stage in ("tool_input", "tool_output"):
                raise ValueError(
                    f"Guardrail stage '{spec.stage}' is not supported on agents. "
                    "Attach tool-level guardrails via tool builders."
                )
            if spec.stage not in ("pre_flight", "input"):
                # Ignore guardrails not applicable to input stages (e.g., output guardrails)
                continue

            guardrail = self._build_input_guardrail(
                spec=spec,
                config=cfg,
                suppress_tripwire=config.suppress_tripwire,
            )
            guardrails.append(guardrail)

        return guardrails

    def build_output_guardrails(
        self,
        config: AgentGuardrailConfig,
    ) -> list[OutputGuardrail[Any]]:
        """Build output guardrails for an agent.

        Creates SDK OutputGuardrail instances for guardrails configured to
        run at the output stage.

        Args:
            config: The agent's guardrail configuration.

        Returns:
            List of OutputGuardrail instances.
        """
        resolved = self._resolve_guardrails(config)
        guardrails: list[OutputGuardrail[Any]] = []

        for spec, cfg in resolved:
            if spec.stage in ("tool_input", "tool_output"):
                raise ValueError(
                    f"Guardrail stage '{spec.stage}' is not supported on agents. "
                    "Attach tool-level guardrails via tool builders."
                )
            if spec.stage != "output":
                # Ignore guardrails not applicable to output stage
                continue

            guardrail = self._build_output_guardrail(
                spec=spec,
                config=cfg,
                suppress_tripwire=config.suppress_tripwire,
            )
            guardrails.append(guardrail)

        return guardrails

    def build_tool_input_guardrails(
        self,
        config: AgentGuardrailConfig,
    ) -> list[ToolInputGuardrail[Any]]:
        """Build tool input guardrails.

        Args:
            config: Guardrail configuration to resolve.

        Returns:
            List of ToolInputGuardrail instances.
        """
        if config.is_empty():
            return []

        resolved = self._resolve_guardrails(config)
        guardrails: list[ToolInputGuardrail[Any]] = []

        for spec, cfg in resolved:
            if spec.stage != "tool_input":
                # Ignore guardrails not applicable to tool input stage
                continue

            guardrails.append(
                self._build_tool_input_guardrail(
                    spec=spec,
                    config=cfg,
                    suppress_tripwire=config.suppress_tripwire,
                )
            )

        return guardrails

    def build_tool_output_guardrails(
        self,
        config: AgentGuardrailConfig,
    ) -> list[ToolOutputGuardrail[Any]]:
        """Build tool output guardrails.

        Args:
            config: Guardrail configuration to resolve.

        Returns:
            List of ToolOutputGuardrail instances.
        """
        if config.is_empty():
            return []

        resolved = self._resolve_guardrails(config)
        guardrails: list[ToolOutputGuardrail[Any]] = []

        for spec, cfg in resolved:
            if spec.stage != "tool_output":
                # Ignore guardrails not applicable to tool output stage
                continue

            guardrails.append(
                self._build_tool_output_guardrail(
                    spec=spec,
                    config=cfg,
                    suppress_tripwire=config.suppress_tripwire,
                )
            )

        return guardrails

    def _resolve_guardrails(
        self,
        config: AgentGuardrailConfig,
    ) -> list[tuple[GuardrailSpec, dict[str, Any]]]:
        """Resolve all guardrails from preset + explicit config.

        Resolution order:
        1. Apply preset (if specified)
        2. Add explicit guardrail_keys with default config
        3. Override with explicit guardrails config

        Args:
            config: The agent's guardrail configuration.

        Returns:
            List of (spec, merged_config) tuples.
        """
        result: dict[str, tuple[GuardrailSpec, dict[str, Any]]] = {}

        # 1. Apply preset first
        if config.preset:
            preset = self._registry.get_preset(config.preset)
            if not preset:
                raise ValueError(f"Guardrail preset '{config.preset}' not found")
            for check_cfg in preset.guardrails:
                if not check_cfg.enabled:
                    continue
                spec = self._registry.get_spec(check_cfg.guardrail_key)
                if spec:
                    merged = {**spec.default_config, **check_cfg.config}
                    result[check_cfg.guardrail_key] = (spec, merged)

        # 2. Apply explicit guardrail keys (with default config)
        for key in config.guardrail_keys:
            spec = self._registry.get_spec(key)
            if not spec:
                raise ValueError(f"Guardrail '{key}' not found in registry")
            if key not in result:
                result[key] = (spec, dict(spec.default_config))

        # 3. Apply explicit guardrail configs (override)
        for check_cfg in config.guardrails:
            spec = self._registry.get_spec(check_cfg.guardrail_key)
            if not spec:
                raise ValueError(
                    f"Guardrail '{check_cfg.guardrail_key}' not found in registry"
                )
            if check_cfg.enabled:
                merged = {**spec.default_config, **check_cfg.config}
                result[check_cfg.guardrail_key] = (spec, merged)
            elif check_cfg.guardrail_key in result:
                # Explicit disable
                del result[check_cfg.guardrail_key]

        return list(result.values())

    def _build_input_guardrail(
        self,
        *,
        spec: GuardrailSpec,
        config: dict[str, Any],
        suppress_tripwire: bool,
    ) -> InputGuardrail[Any]:
        """Build an SDK InputGuardrail from a spec.

        Args:
            spec: The guardrail specification.
            config: Validated configuration for this guardrail.
            suppress_tripwire: Whether to suppress tripwire exceptions.

        Returns:
            SDK InputGuardrail instance.
        """
        check_fn = self._get_check_fn(spec)

        async def guardrail_fn(ctx: Any, agent: Any, input_data: Any) -> GuardrailFunctionOutput:
            """Wrapper function that executes the guardrail check."""
            try:
                # Validate config against schema
                validated = spec.validate_config(config)
                validated_dict = validated.model_dump()

                # Extract conversation history if available
                conversation_history = None
                if spec.uses_conversation_history and hasattr(ctx, "context"):
                    history = getattr(ctx.context, "conversation_history", None)
                    if history:
                        conversation_history = history

                # Execute the check
                result = await check_fn(
                    content=str(input_data),
                    config=validated_dict,
                    conversation_history=conversation_history,
                    context={
                        "agent_name": getattr(agent, "name", "unknown"),
                        "stage": spec.stage,
                    },
                )

                output_info = result.to_output_info()
                output_info["guardrail_name"] = spec.display_name

                return GuardrailFunctionOutput(
                    output_info=output_info,
                    tripwire_triggered=result.tripwire_triggered and not suppress_tripwire,
                )

            except Exception as e:
                logger.exception(
                    "Guardrail '%s' raised an error: %s", spec.key, e
                )
                return GuardrailFunctionOutput(
                    output_info={
                        "guardrail_name": spec.display_name,
                        "error": str(e),
                        "flagged": False,
                    },
                    tripwire_triggered=spec.tripwire_on_error and not suppress_tripwire,
                )

        return InputGuardrail(
            guardrail_function=guardrail_fn,
            name=spec.display_name,
        )

    def _build_output_guardrail(
        self,
        *,
        spec: GuardrailSpec,
        config: dict[str, Any],
        suppress_tripwire: bool,
    ) -> OutputGuardrail[Any]:
        """Build an SDK OutputGuardrail from a spec.

        Args:
            spec: The guardrail specification.
            config: Validated configuration for this guardrail.
            suppress_tripwire: Whether to suppress tripwire exceptions.

        Returns:
            SDK OutputGuardrail instance.
        """
        check_fn = self._get_check_fn(spec)

        async def guardrail_fn(ctx: Any, agent: Any, output_data: Any) -> GuardrailFunctionOutput:
            """Wrapper function that executes the guardrail check."""
            try:
                validated = spec.validate_config(config)
                validated_dict = validated.model_dump()

                conversation_history = None
                if spec.uses_conversation_history and hasattr(ctx, "context"):
                    history = getattr(ctx.context, "conversation_history", None)
                    if history:
                        conversation_history = history

                result = await check_fn(
                    content=str(output_data),
                    config=validated_dict,
                    conversation_history=conversation_history,
                    context={
                        "agent_name": getattr(agent, "name", "unknown"),
                        "stage": spec.stage,
                    },
                )

                output_info = result.to_output_info()
                output_info["guardrail_name"] = spec.display_name

                return GuardrailFunctionOutput(
                    output_info=output_info,
                    tripwire_triggered=result.tripwire_triggered and not suppress_tripwire,
                )

            except Exception as e:
                logger.exception(
                    "Guardrail '%s' raised an error: %s", spec.key, e
                )
                return GuardrailFunctionOutput(
                    output_info={
                        "guardrail_name": spec.display_name,
                        "error": str(e),
                        "flagged": False,
                    },
                    tripwire_triggered=spec.tripwire_on_error and not suppress_tripwire,
                )

        return OutputGuardrail(
            guardrail_function=guardrail_fn,
            name=spec.display_name,
        )

    def _build_tool_input_guardrail(
        self,
        *,
        spec: GuardrailSpec,
        config: dict[str, Any],
        suppress_tripwire: bool,
    ) -> ToolInputGuardrail[Any]:
        """Build a tool input guardrail."""
        check_fn = self._get_check_fn(spec)

        async def guardrail_fn(data: ToolInputGuardrailData) -> ToolGuardrailFunctionOutput:
            try:
                validated = spec.validate_config(config)
                validated_dict = validated.model_dump()

                conversation_history = None
                ctx = getattr(data, "context", None)
                if spec.uses_conversation_history and ctx is not None and hasattr(ctx, "context"):
                    history = getattr(ctx.context, "conversation_history", None)
                    if history:
                        conversation_history = history

                agent_obj = getattr(data, "agent", None)
                result = await check_fn(
                    content=str(getattr(ctx, "tool_arguments", "")),
                    config=validated_dict,
                    conversation_history=conversation_history,
                    context={
                        "agent_name": getattr(agent_obj, "name", "unknown"),
                        "tool_name": getattr(ctx, "tool_name", "unknown"),
                        "stage": spec.stage,
                    },
                )

                output_info = result.to_output_info()
                output_info["guardrail_name"] = spec.display_name

                behavior = (
                    RaiseExceptionBehavior(type="raise_exception")
                    if result.tripwire_triggered and not suppress_tripwire
                    else AllowBehavior(type="allow")
                )

                return ToolGuardrailFunctionOutput(output_info=output_info, behavior=behavior)
            except Exception as e:  # pragma: no cover - defensive logging path
                logger.exception("Tool guardrail '%s' raised an error: %s", spec.key, e)
                behavior = (
                    RaiseExceptionBehavior(type="raise_exception")
                    if spec.tripwire_on_error and not suppress_tripwire
                    else AllowBehavior(type="allow")
                )
                return ToolGuardrailFunctionOutput(
                    output_info={
                        "guardrail_name": spec.display_name,
                        "error": str(e),
                        "flagged": False,
                    },
                    behavior=behavior,
                )

        return ToolInputGuardrail(
            guardrail_function=guardrail_fn,
            name=spec.display_name,
        )

    def _build_tool_output_guardrail(
        self,
        *,
        spec: GuardrailSpec,
        config: dict[str, Any],
        suppress_tripwire: bool,
    ) -> ToolOutputGuardrail[Any]:
        """Build a tool output guardrail."""
        check_fn = self._get_check_fn(spec)

        async def guardrail_fn(data: ToolOutputGuardrailData) -> ToolGuardrailFunctionOutput:
            try:
                validated = spec.validate_config(config)
                validated_dict = validated.model_dump()

                conversation_history = None
                ctx = getattr(data, "context", None)
                if spec.uses_conversation_history and ctx is not None and hasattr(ctx, "context"):
                    history = getattr(ctx.context, "conversation_history", None)
                    if history:
                        conversation_history = history

                agent_obj = getattr(data, "agent", None)
                result = await check_fn(
                    content=str(getattr(data, "output", "")),
                    config=validated_dict,
                    conversation_history=conversation_history,
                    context={
                        "agent_name": getattr(agent_obj, "name", "unknown"),
                        "tool_name": getattr(ctx, "tool_name", "unknown"),
                        "stage": spec.stage,
                    },
                )

                output_info = result.to_output_info()
                output_info["guardrail_name"] = spec.display_name

                behavior = (
                    RaiseExceptionBehavior(type="raise_exception")
                    if result.tripwire_triggered and not suppress_tripwire
                    else AllowBehavior(type="allow")
                )

                return ToolGuardrailFunctionOutput(output_info=output_info, behavior=behavior)
            except Exception as e:  # pragma: no cover - defensive logging path
                logger.exception("Tool guardrail '%s' raised an error: %s", spec.key, e)
                behavior = (
                    RaiseExceptionBehavior(type="raise_exception")
                    if spec.tripwire_on_error and not suppress_tripwire
                    else AllowBehavior(type="allow")
                )
                return ToolGuardrailFunctionOutput(
                    output_info={
                        "guardrail_name": spec.display_name,
                        "error": str(e),
                        "flagged": False,
                    },
                    behavior=behavior,
                )

        return ToolOutputGuardrail(
            guardrail_function=guardrail_fn,
            name=spec.display_name,
        )

    def _get_check_fn(self, spec: GuardrailSpec) -> CheckFn:
        """Import and cache the check function.

        Args:
            spec: The guardrail specification.

        Returns:
            The async check function.
        """
        if spec.key not in self._check_fn_cache:
            self._check_fn_cache[spec.key] = self._import_check_fn(spec.check_fn_path)
        return self._check_fn_cache[spec.key]

    @staticmethod
    def _import_check_fn(path: str) -> CheckFn:
        """Import a check function from a dotted path.

        Supports both colon and dot notation:
        - "app.guardrails.checks.pii_detection.check:run_check"
        - "app.guardrails.checks.pii_detection.check.run_check"

        Args:
            path: Dotted path to the check function.

        Returns:
            The imported check function.

        Raises:
            ValueError: If the path is invalid or function not found.
        """
        if ":" in path:
            module_path, attr = path.split(":", 1)
        elif "." in path:
            module_path, attr = path.rsplit(".", 1)
        else:
            raise ValueError(f"Invalid check function path: '{path}'")

        try:
            module = importlib.import_module(module_path)
        except ImportError as e:
            raise ValueError(f"Could not import module '{module_path}': {e}") from e

        fn = getattr(module, attr, None)
        if fn is None:
            raise ValueError(f"Check function '{attr}' not found in '{module_path}'")

        return fn


__all__ = ["GuardrailBuilder"]
