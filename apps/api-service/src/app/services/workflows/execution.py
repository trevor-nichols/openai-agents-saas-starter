"""Shared logic for executing a single workflow step."""

from __future__ import annotations

from typing import Any

from app.domain.ai import AgentRunResult, RunOptions
from app.workflows.schema_utils import validate_against_schema
from app.workflows.specs import WorkflowStep


async def execute_agent_step(
    step: WorkflowStep,
    step_input: Any,
    provider,
    runtime_ctx,
    conversation_id: str,
    metadata: dict[str, Any],
    options: RunOptions | None,
    session_handle: Any | None = None,
) -> tuple[Any | None, AgentRunResult]:
    result = await provider.runtime.run(
        step.agent_key,
        step_input,
        # Avoid passing our internal conversation UUID to the provider; OpenAI
        # Responses API expects `conv_*` ids. Session handles keep continuity.
        conversation_id=None,
        metadata=metadata,
        options=options,
        session=session_handle,
    )

    chosen_output: Any | None = None
    if result.structured_output is not None:
        chosen_output = result.structured_output
    elif result.response_text is not None:
        chosen_output = result.response_text
    elif result.final_output is not None:
        chosen_output = result.final_output

    fallback_response_text = result.response_text
    if fallback_response_text is None and result.final_output is not None:
        fallback_response_text = str(result.final_output)

    safe_metadata: dict[str, Any] = {
        k: v for k, v in (metadata or {}).items() if k != "prompt_runtime_ctx"
    }
    if isinstance(result.metadata, dict):
        safe_metadata = {**safe_metadata, **result.metadata}

    response = AgentRunResult(
        final_output=chosen_output,
        response_text=fallback_response_text,
        structured_output=result.structured_output,
        response_id=result.response_id,
        usage=result.usage,
        metadata=safe_metadata or None,
        tool_outputs=result.tool_outputs,
    )

    validate_against_schema(
        step.output_schema,
        chosen_output,
        label=f"step '{step.display_name()}' output",
    )
    return chosen_output, response


__all__ = ["execute_agent_step"]
