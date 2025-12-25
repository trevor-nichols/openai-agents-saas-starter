"""Guardrail runtime helpers for execution, output shaping, and event emission."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar

from agents.guardrail import GuardrailFunctionOutput
from agents.tool_guardrails import (
    AllowBehavior,
    RaiseExceptionBehavior,
    ToolGuardrailFunctionOutput,
)

from app.guardrails._shared.events import emit_guardrail_event
from app.guardrails._shared.specs import GuardrailCheckResult, GuardrailSpec

if TYPE_CHECKING:
    from collections.abc import Awaitable

    CheckFn = Callable[..., Awaitable[GuardrailCheckResult]]

OutputT = TypeVar("OutputT")

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class GuardrailExecutionContext:
    """Runtime context used to execute a guardrail check."""

    content: str
    agent_name: str
    stage: str
    conversation_history: list[dict[str, str]] | None = None
    tool_name: str | None = None
    tool_call_id: str | None = None


def build_agent_execution_context(
    *,
    spec: GuardrailSpec,
    ctx: Any,
    agent: Any,
    content: Any,
) -> GuardrailExecutionContext:
    """Create execution context for agent-level guardrails."""
    return GuardrailExecutionContext(
        content=str(content),
        agent_name=getattr(agent, "name", "unknown"),
        stage=spec.stage,
        conversation_history=_extract_conversation_history(spec, ctx),
    )


def build_tool_execution_context(
    *,
    spec: GuardrailSpec,
    data: Any,
    content: Any,
) -> GuardrailExecutionContext:
    """Create execution context for tool-level guardrails."""
    ctx = getattr(data, "context", None)
    return GuardrailExecutionContext(
        content=str(content),
        agent_name=getattr(getattr(data, "agent", None), "name", "unknown"),
        stage=spec.stage,
        conversation_history=_extract_conversation_history(spec, ctx),
        tool_name=_resolve_tool_name(data, ctx),
        tool_call_id=getattr(data, "tool_call_id", None),
    )


class GuardrailRuntime:
    """Executes guardrails and shapes outputs consistently."""

    def __init__(self, *, logger_override: logging.Logger | None = None) -> None:
        self._logger = logger_override or logger

    async def execute(
        self,
        *,
        spec: GuardrailSpec,
        check_fn: CheckFn,
        config: dict[str, Any],
        exec_ctx: GuardrailExecutionContext,
        suppress_tripwire: bool,
        output_builder: Callable[[GuardrailSpec, GuardrailCheckResult, bool], OutputT],
        error_builder: Callable[[GuardrailSpec, Exception, bool], OutputT],
    ) -> OutputT:
        try:
            result = await check_fn(
                content=exec_ctx.content,
                config=config,
                conversation_history=exec_ctx.conversation_history,
                context=_build_runtime_context(exec_ctx),
            )
        except Exception as exc:
            self._logger.exception(
                "Guardrail '%s' raised an error: %s",
                spec.key,
                exc,
            )
            return error_builder(spec, exc, suppress_tripwire)

        output = output_builder(spec, result, suppress_tripwire)
        emit_guardrail_result(
            spec=spec,
            exec_ctx=exec_ctx,
            result=result,
            suppressed=suppress_tripwire,
        )
        return output


def build_agent_output(
    spec: GuardrailSpec, result: GuardrailCheckResult, suppress_tripwire: bool
) -> GuardrailFunctionOutput:
    output_info = _build_output_info(spec, result)
    return GuardrailFunctionOutput(
        output_info=output_info,
        tripwire_triggered=result.tripwire_triggered and not suppress_tripwire,
    )


def build_agent_error_output(
    spec: GuardrailSpec, exc: Exception, suppress_tripwire: bool
) -> GuardrailFunctionOutput:
    return GuardrailFunctionOutput(
        output_info=_build_error_output_info(spec, exc),
        tripwire_triggered=spec.tripwire_on_error and not suppress_tripwire,
    )


def build_tool_output(
    spec: GuardrailSpec, result: GuardrailCheckResult, suppress_tripwire: bool
) -> ToolGuardrailFunctionOutput:
    behavior = _behavior_for_tripwire(result.tripwire_triggered, suppress_tripwire)
    return ToolGuardrailFunctionOutput(
        output_info=_build_output_info(spec, result),
        behavior=behavior,
    )


def build_tool_error_output(
    spec: GuardrailSpec, exc: Exception, suppress_tripwire: bool
) -> ToolGuardrailFunctionOutput:
    behavior = _behavior_for_tripwire(spec.tripwire_on_error, suppress_tripwire)
    return ToolGuardrailFunctionOutput(
        output_info=_build_error_output_info(spec, exc),
        behavior=behavior,
    )


def emit_guardrail_result(
    *,
    spec: GuardrailSpec,
    exec_ctx: GuardrailExecutionContext,
    result: GuardrailCheckResult,
    suppressed: bool,
) -> None:
    payload = {
        "kind": "guardrail_result",
        "guardrail_stage": exec_ctx.stage,
        "guardrail_key": spec.key,
        "guardrail_name": spec.display_name,
        "guardrail_tripwire_triggered": bool(result.tripwire_triggered),
        "guardrail_suppressed": bool(suppressed),
        "guardrail_flagged": bool(result.info.get("flagged")) if result.info else None,
        "guardrail_confidence": result.confidence,
        "guardrail_masked_content": result.masked_content,
        "guardrail_token_usage": result.token_usage,
        "guardrail_details": result.info or {},
        "tool_name": exec_ctx.tool_name,
        "tool_call_id": exec_ctx.tool_call_id,
    }
    emit_guardrail_event(payload)


def _build_runtime_context(exec_ctx: GuardrailExecutionContext) -> dict[str, Any]:
    context = {
        "agent_name": exec_ctx.agent_name,
        "stage": exec_ctx.stage,
    }
    if exec_ctx.tool_name is not None:
        context["tool_name"] = exec_ctx.tool_name
    return context


def _build_output_info(spec: GuardrailSpec, result: GuardrailCheckResult) -> dict[str, Any]:
    output_info = result.to_output_info()
    output_info["guardrail_name"] = spec.display_name
    output_info["stage"] = spec.stage
    return output_info


def _build_error_output_info(spec: GuardrailSpec, exc: Exception) -> dict[str, Any]:
    return {
        "guardrail_name": spec.display_name,
        "stage": spec.stage,
        "error": str(exc),
        "flagged": False,
    }


def _behavior_for_tripwire(tripwire_triggered: bool, suppress_tripwire: bool) -> Any:
    if tripwire_triggered and not suppress_tripwire:
        return RaiseExceptionBehavior(type="raise_exception")
    return AllowBehavior(type="allow")


def _extract_conversation_history(
    spec: GuardrailSpec, ctx: Any | None
) -> list[dict[str, str]] | None:
    if not spec.uses_conversation_history or ctx is None:
        return None
    inner = getattr(ctx, "context", None)
    if inner is None:
        return None
    history = getattr(inner, "conversation_history", None)
    return history or None


def _resolve_tool_name(data: Any, ctx: Any | None) -> str:
    fallback = getattr(ctx, "tool_name", "unknown") if ctx else "unknown"
    return getattr(data, "tool_name", fallback)


__all__ = [
    "GuardrailExecutionContext",
    "GuardrailRuntime",
    "build_agent_execution_context",
    "build_tool_execution_context",
    "build_agent_output",
    "build_agent_error_output",
    "build_tool_output",
    "build_tool_error_output",
    "emit_guardrail_result",
]
