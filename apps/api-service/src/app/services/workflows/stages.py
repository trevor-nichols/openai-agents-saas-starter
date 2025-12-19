"""Non-streaming stage execution helpers for the workflow runner."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from app.domain.ai import RunOptions
from app.services.workflows.execution import execute_agent_step
from app.services.workflows.hooks import apply_reducer, evaluate_guard, run_mapper
from app.services.workflows.recording import WorkflowRunRecorder
from app.services.workflows.types import WorkflowStepResult
from app.workflows._shared.schema_utils import schema_to_json_schema
from app.workflows._shared.specs import WorkflowSpec, WorkflowStage, WorkflowStep


async def run_sequential_stage(
    *,
    run_id: str,
    workflow: WorkflowSpec,
    stage: WorkflowStage,
    current_input: Any,
    steps_results: list[WorkflowStepResult],
    provider,
    runtime_ctx,
    conversation_id: str,
    recorder: WorkflowRunRecorder,
    check_cancel: Callable[[], None],
    session_getter,
    ingest_session_delta,
    session_handle,
) -> Any:
    for step in stage.steps:
        check_cancel()
        if step.guard and not await evaluate_guard(step.guard, current_input, steps_results):
            continue

        step_input = current_input
        if step.input_mapper:
            step_input = await run_mapper(step.input_mapper, current_input, steps_results)

        options = RunOptions(max_turns=step.max_turns) if step.max_turns is not None else None
        metadata = {
            "prompt_runtime_ctx": runtime_ctx,
            "workflow_key": workflow.key,
            "workflow_run_id": run_id,
            "stage_name": stage.name,
        }
        pre_items = await session_getter()
        chosen_output, response = await execute_agent_step(
            step,
            step_input,
            provider,
            runtime_ctx,
            conversation_id,
            metadata,
            options,
            session_handle=session_handle,
        )

        await recorder.step_end(
            run_id,
            sequence_no=len(steps_results),
            step_name=step.display_name(),
            step_agent=step.agent_key,
            response=response,
            status="succeeded",
            stage_name=stage.name,
            parallel_group=None,
            branch_index=None,
        )

        steps_results.append(
            WorkflowStepResult(
                name=step.display_name(),
                agent_key=step.agent_key,
                response=response,
                stage_name=stage.name,
                output_schema=schema_to_json_schema(step.output_schema),
            )
        )
        await ingest_session_delta(
            pre_items=pre_items,
            agent=step.agent_key,
            model=_response_model(response),
            response_id=response.response_id,
        )
        current_input = response.final_output
    return current_input


async def run_parallel_stage(
    *,
    run_id: str,
    workflow: WorkflowSpec,
    stage: WorkflowStage,
    current_input: Any,
    steps_results: list[WorkflowStepResult],
    provider,
    runtime_ctx,
    conversation_id: str,
    recorder: WorkflowRunRecorder,
    check_cancel: Callable[[], None],
    session_getter,
    ingest_session_delta,
    workflow_run_id: str,
    session_handle,
) -> Any:
    _ = workflow_run_id
    branch_specs: list[tuple[int, WorkflowStep, Any, RunOptions | None, dict[str, Any]]]=[]
    for idx, step in enumerate(stage.steps):
        check_cancel()
        if step.guard and not await evaluate_guard(step.guard, current_input, steps_results):
            continue
        step_input = current_input
        if step.input_mapper:
            step_input = await run_mapper(step.input_mapper, current_input, steps_results)
        options = RunOptions(max_turns=step.max_turns) if step.max_turns is not None else None
        metadata = {
            "prompt_runtime_ctx": runtime_ctx,
            "workflow_key": workflow.key,
            "workflow_run_id": run_id,
            "stage_name": stage.name,
            "parallel_group": stage.name,
            "branch_index": idx,
        }
        branch_specs.append((idx, step, step_input, options, metadata))

    if not branch_specs:
        # Nothing to run in this stage; preserve current input to mirror sequential behavior.
        return current_input

    async def _run_branch(
        spec: tuple[int, WorkflowStep, Any, RunOptions | None, dict[str, Any]]
    ):
        idx, step, step_input, options, metadata = spec
        return idx, step, await execute_agent_step(
            step,
            step_input,
            provider,
            runtime_ctx,
            conversation_id,
            metadata,
            options,
            session_handle=session_handle,
        )

    pre_items = await session_getter()
    branch_results = await asyncio.gather(*[_run_branch(spec) for spec in branch_specs])
    post_items = await session_getter()
    delta_items = post_items[len(pre_items) :] if post_items else []
    outputs: list[Any] = []
    for idx, step, (chosen_output, response) in sorted(branch_results, key=lambda x: x[0]):
        outputs.append(chosen_output)
        await recorder.step_end(
            run_id,
            sequence_no=len(steps_results),
            step_name=step.display_name(),
            step_agent=step.agent_key,
            response=response,
            status="succeeded",
            stage_name=stage.name,
            parallel_group=stage.name,
            branch_index=idx,
        )
        steps_results.append(
            WorkflowStepResult(
                name=step.display_name(),
                agent_key=step.agent_key,
                response=response,
                stage_name=stage.name,
                parallel_group=stage.name,
                branch_index=idx,
                output_schema=schema_to_json_schema(step.output_schema),
            )
        )

    next_input = await apply_reducer(stage.reducer, outputs, steps_results)

    def _branch_index_of(item: Any) -> int | None:
        def _as_int(value: Any) -> int | None:
            if isinstance(value, int):
                return value
            if isinstance(value, str) and value.isdigit():
                return int(value)
            return None

        if isinstance(item, dict):
            direct = _as_int(item.get("branch_index"))
            if direct is not None:
                return direct
            metadata = item.get("metadata")
            if isinstance(metadata, dict):
                meta_val = _as_int(metadata.get("branch_index"))
                if meta_val is not None:
                    return meta_val
        return None

    branch_meta = {
        idx: (
            step.agent_key,
            _response_model(response),
            getattr(response, "response_id", None),
        )
        for idx, step, (_chosen_output, response) in sorted(branch_results, key=lambda x: x[0])
    }

    for item in delta_items:
        branch_idx = _branch_index_of(item)
        agent = model = response_id = None
        if branch_idx is not None and branch_idx in branch_meta:
            agent, model, response_id = branch_meta[branch_idx]
        await ingest_session_delta(
            pre_items=[],
            agent=agent,
            model=model,
            response_id=response_id,
            session_items=[item],
        )
    return next_input


def _response_model(response) -> str | None:
    metadata = getattr(response, "metadata", None)
    if isinstance(metadata, dict):
        model = metadata.get("model")
        return str(model) if model is not None else None
    return None


__all__ = ["run_parallel_stage", "run_sequential_stage"]
