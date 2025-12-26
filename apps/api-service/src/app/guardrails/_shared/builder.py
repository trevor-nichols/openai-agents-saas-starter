"""Constructs SDK-compatible guardrail functions from specifications.

This module provides the `GuardrailBuilder` class that transforms declarative
`GuardrailSpec` instances into concrete guardrail functions compatible with
the OpenAI Agents SDK.

Architecture mirrors the AgentBuilder pattern while delegating resolution and
runtime execution to focused helper modules.
"""

from __future__ import annotations

import logging
from typing import Any

from agents import InputGuardrail, OutputGuardrail
from agents.tool_guardrails import (
    ToolInputGuardrail,
    ToolInputGuardrailData,
    ToolOutputGuardrail,
    ToolOutputGuardrailData,
)

from app.guardrails._shared.registry import GuardrailRegistry
from app.guardrails._shared.resolver import GuardrailResolver, ResolvedGuardrail
from app.guardrails._shared.runtime import (
    GuardrailRuntime,
    build_agent_error_output,
    build_agent_execution_context,
    build_agent_output,
    build_tool_error_output,
    build_tool_execution_context,
    build_tool_output,
)
from app.guardrails._shared.specs import AgentGuardrailConfig, GuardrailSpec

logger = logging.getLogger(__name__)


class GuardrailBuilder:
    """Builds SDK guardrail functions from declarative specs."""

    def __init__(self, registry: GuardrailRegistry) -> None:
        """Initialize the builder.

        Args:
            registry: The guardrail registry containing specs and presets.
        """
        self._resolver = GuardrailResolver(registry)
        self._runtime = GuardrailRuntime(logger_override=logger)

    def build_input_guardrails(
        self,
        config: AgentGuardrailConfig,
    ) -> list[InputGuardrail[Any]]:
        """Build input guardrails for an agent."""
        if config.is_empty():
            return []

        resolved = self._resolver.resolve(config)
        guardrails: list[InputGuardrail[Any]] = []

        for resolved_guardrail in resolved:
            spec = resolved_guardrail.spec
            self._assert_stage_allowed(spec)
            if spec.stage not in ("pre_flight", "input"):
                continue

            guardrails.append(
                self._build_input_guardrail(
                    resolved=resolved_guardrail,
                    suppress_tripwire=config.suppress_tripwire,
                )
            )

        return guardrails

    def build_output_guardrails(
        self,
        config: AgentGuardrailConfig,
    ) -> list[OutputGuardrail[Any]]:
        """Build output guardrails for an agent."""
        if config.is_empty():
            return []

        resolved = self._resolver.resolve(config)
        guardrails: list[OutputGuardrail[Any]] = []

        for resolved_guardrail in resolved:
            spec = resolved_guardrail.spec
            self._assert_stage_allowed(spec)
            if spec.stage != "output":
                continue

            guardrails.append(
                self._build_output_guardrail(
                    resolved=resolved_guardrail,
                    suppress_tripwire=config.suppress_tripwire,
                )
            )

        return guardrails

    def build_tool_input_guardrails(
        self,
        config: AgentGuardrailConfig,
    ) -> list[ToolInputGuardrail[Any]]:
        """Build tool input guardrails."""
        if config.is_empty():
            return []

        resolved = self._resolver.resolve(config)
        guardrails: list[ToolInputGuardrail[Any]] = []

        for resolved_guardrail in resolved:
            if resolved_guardrail.spec.stage != "tool_input":
                continue
            guardrails.append(
                self._build_tool_input_guardrail(
                    resolved=resolved_guardrail,
                    suppress_tripwire=config.suppress_tripwire,
                )
            )

        return guardrails

    def build_tool_output_guardrails(
        self,
        config: AgentGuardrailConfig,
    ) -> list[ToolOutputGuardrail[Any]]:
        """Build tool output guardrails."""
        if config.is_empty():
            return []

        resolved = self._resolver.resolve(config)
        guardrails: list[ToolOutputGuardrail[Any]] = []

        for resolved_guardrail in resolved:
            if resolved_guardrail.spec.stage != "tool_output":
                continue
            guardrails.append(
                self._build_tool_output_guardrail(
                    resolved=resolved_guardrail,
                    suppress_tripwire=config.suppress_tripwire,
                )
            )

        return guardrails

    def _build_input_guardrail(
        self,
        *,
        resolved: ResolvedGuardrail,
        suppress_tripwire: bool,
    ) -> InputGuardrail[Any]:
        spec = resolved.spec

        async def guardrail_fn(ctx: Any, agent: Any, input_data: Any):
            exec_ctx = build_agent_execution_context(
                spec=spec,
                ctx=ctx,
                agent=agent,
                content=input_data,
            )
            return await self._runtime.execute(
                spec=spec,
                check_fn=resolved.check_fn,
                config=resolved.config_dict(),
                exec_ctx=exec_ctx,
                suppress_tripwire=suppress_tripwire,
                output_builder=build_agent_output,
                error_builder=build_agent_error_output,
            )

        return InputGuardrail(
            guardrail_function=guardrail_fn,
            name=spec.display_name,
        )

    def _build_output_guardrail(
        self,
        *,
        resolved: ResolvedGuardrail,
        suppress_tripwire: bool,
    ) -> OutputGuardrail[Any]:
        spec = resolved.spec

        async def guardrail_fn(ctx: Any, agent: Any, output_data: Any):
            exec_ctx = build_agent_execution_context(
                spec=spec,
                ctx=ctx,
                agent=agent,
                content=output_data,
            )
            return await self._runtime.execute(
                spec=spec,
                check_fn=resolved.check_fn,
                config=resolved.config_dict(),
                exec_ctx=exec_ctx,
                suppress_tripwire=suppress_tripwire,
                output_builder=build_agent_output,
                error_builder=build_agent_error_output,
            )

        return OutputGuardrail(
            guardrail_function=guardrail_fn,
            name=spec.display_name,
        )

    def _build_tool_input_guardrail(
        self,
        *,
        resolved: ResolvedGuardrail,
        suppress_tripwire: bool,
    ) -> ToolInputGuardrail[Any]:
        spec = resolved.spec

        async def guardrail_fn(data: ToolInputGuardrailData):
            exec_ctx = build_tool_execution_context(
                spec=spec,
                data=data,
                content=getattr(data, "tool_arguments", ""),
            )
            return await self._runtime.execute(
                spec=spec,
                check_fn=resolved.check_fn,
                config=resolved.config_dict(),
                exec_ctx=exec_ctx,
                suppress_tripwire=suppress_tripwire,
                output_builder=build_tool_output,
                error_builder=build_tool_error_output,
            )

        return ToolInputGuardrail(
            guardrail_function=guardrail_fn,
            name=spec.display_name,
        )

    def _build_tool_output_guardrail(
        self,
        *,
        resolved: ResolvedGuardrail,
        suppress_tripwire: bool,
    ) -> ToolOutputGuardrail[Any]:
        spec = resolved.spec

        async def guardrail_fn(data: ToolOutputGuardrailData):
            exec_ctx = build_tool_execution_context(
                spec=spec,
                data=data,
                content=getattr(data, "output", ""),
            )
            return await self._runtime.execute(
                spec=spec,
                check_fn=resolved.check_fn,
                config=resolved.config_dict(),
                exec_ctx=exec_ctx,
                suppress_tripwire=suppress_tripwire,
                output_builder=build_tool_output,
                error_builder=build_tool_error_output,
            )

        return ToolOutputGuardrail(
            guardrail_function=guardrail_fn,
            name=spec.display_name,
        )

    @staticmethod
    def _assert_stage_allowed(spec: GuardrailSpec) -> None:
        if spec.stage in ("tool_input", "tool_output"):
            raise ValueError(
                f"Guardrail stage '{spec.stage}' is not supported on agents. "
                "Attach tool-level guardrails via tool builders."
            )


__all__ = ["GuardrailBuilder"]
