"""Streaming stage execution helpers for the workflow runner."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Callable
from typing import Any

from app.domain.ai import AgentRunResult, RunOptions
from app.domain.ai.models import AgentStreamEvent
from app.services.workflows.hooks import apply_reducer, evaluate_guard, run_mapper
from app.services.workflows.recording import WorkflowRunRecorder
from app.services.workflows.types import WorkflowStepResult
from app.workflows._shared.schema_utils import schema_to_json_schema, validate_against_schema
from app.workflows._shared.specs import WorkflowSpec, WorkflowStage, WorkflowStep


async def stream_sequential_stage(
    *,
    run_id: str,
    workflow: WorkflowSpec,
    stage: WorkflowStage,
    current_input: Any,
    prior_steps: list[WorkflowStepResult],
    provider,
    runtime_ctx,
    conversation_id: str,
    recorder: WorkflowRunRecorder,
    check_cancel: Callable[[], None],
    session_getter,
    ingest_session_delta,
    session_handle,
) -> AsyncIterator[AgentStreamEvent]:
    for step in stage.steps:
        check_cancel()
        if step.guard and not await evaluate_guard(step.guard, current_input, prior_steps):
            continue

        step_input = current_input
        if step.input_mapper:
            step_input = await run_mapper(step.input_mapper, current_input, prior_steps)

        options = RunOptions(max_turns=step.max_turns) if step.max_turns is not None else None
        metadata = {
            "prompt_runtime_ctx": runtime_ctx,
            "workflow_key": workflow.key,
            "workflow_run_id": run_id,
            "stage_name": stage.name,
        }
        pre_items = await session_getter()
        stream_handle = provider.runtime.run_stream(
            step.agent_key,
            step_input,
            # Avoid passing internal UUIDs to provider; session carries continuity.
            conversation_id=None,
            metadata=metadata,
            options=options,
            session=session_handle,
        )

        last_text: str | None = None
        text_buffer: list[str] = []
        last_structured: Any | None = None
        step_metadata = getattr(stream_handle, "metadata", None)
        async for event in stream_handle.events():
            check_cancel()
            event.conversation_id = conversation_id
            event.agent = event.agent or step.agent_key
            event.step_name = step.display_name()
            event.step_agent = step.agent_key
            event.stage_name = stage.name
            event.parallel_group = None
            event.branch_index = None
            event.metadata = {
                **(event.metadata or {}),
                "workflow_key": workflow.key,
                "workflow_run_id": run_id,
                "step_name": step.display_name(),
                "step_agent": step.agent_key,
                "stage_name": stage.name,
            }
            if step_metadata is None and isinstance(event.metadata, dict):
                step_metadata = event.metadata
            if event.response_text:
                last_text = event.response_text
            if event.text_delta:
                text_buffer.append(event.text_delta)
            if event.structured_output is not None:
                last_structured = event.structured_output
            yield event
            if event.is_terminal:
                break

        if not last_text and text_buffer:
            last_text = "".join(text_buffer)

        chosen_output = None
        if last_structured is not None:
            chosen_output = last_structured
        elif last_text is not None:
            chosen_output = last_text

        validate_against_schema(
            step.output_schema,
            chosen_output,
            label=f"step '{step.display_name()}' output",
        )

        step_result = WorkflowStepResult(
            name=step.display_name(),
            agent_key=step.agent_key,
            response=AgentRunResult(
                final_output=chosen_output,
                response_text=last_text
                if last_text is not None
                else (
                    json.dumps(last_structured, ensure_ascii=False)
                    if last_structured is not None
                    else None
                ),
                structured_output=last_structured,
                response_id=getattr(stream_handle, "last_response_id", None),
                usage=getattr(stream_handle, "usage", None),
                metadata=step_metadata,
            ),
            stage_name=stage.name,
            output_schema=schema_to_json_schema(step.output_schema),
        )
        prior_steps.append(step_result)

        await recorder.step_end(
            run_id,
            sequence_no=len(prior_steps) - 1,
            step_name=step.display_name(),
            step_agent=step.agent_key,
            response=step_result.response,
            status="succeeded",
            stage_name=stage.name,
            parallel_group=None,
            branch_index=None,
        )

        if chosen_output is not None:
            current_input = chosen_output
        await ingest_session_delta(
            pre_items=pre_items,
            agent=step.agent_key,
            model=_response_model(step_result.response),
            response_id=step_result.response.response_id,
        )


async def stream_parallel_stage(
    *,
    run_id: str,
    workflow: WorkflowSpec,
    stage: WorkflowStage,
    current_input: Any,
    prior_steps: list[WorkflowStepResult],
    provider,
    runtime_ctx,
    conversation_id: str,
    recorder: WorkflowRunRecorder,
    check_cancel: Callable[[], None],
    stage_state: dict[str, Any],
    session_getter,
    ingest_session_delta,
    session_handle,
    workflow_run_id: str,
) -> AsyncIterator[AgentStreamEvent]:
    _ = workflow_run_id
    branch_specs: list[tuple[int, WorkflowStep, Any, RunOptions | None, dict[str, Any]]] = []
    for idx, step in enumerate(stage.steps):
        check_cancel()
        if step.guard and not await evaluate_guard(step.guard, current_input, prior_steps):
            continue
        step_input = current_input
        if step.input_mapper:
            step_input = await run_mapper(step.input_mapper, current_input, prior_steps)
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
        stage_state["next_input"] = current_input
        return

    queue: asyncio.Queue[Any] = asyncio.Queue()
    branch_results: list[tuple[int, WorkflowStepResult]] = []
    pre_items = await session_getter()

    async def _consume_branch(
        spec: tuple[int, WorkflowStep, Any, RunOptions | None, dict[str, Any]]
    ):
        idx, step, step_input, options, metadata = spec
        try:
            stream_handle = provider.runtime.run_stream(
                step.agent_key,
                step_input,
                conversation_id=None,
                metadata=metadata,
                options=options,
                session=session_handle,
            )
            last_text: str | None = None
            text_buffer: list[str] = []
            last_structured: Any | None = None
            step_metadata = getattr(stream_handle, "metadata", None)
            async for event in stream_handle.events():
                check_cancel()
                event.conversation_id = conversation_id
                event.agent = event.agent or step.agent_key
                event.step_name = step.display_name()
                event.step_agent = step.agent_key
                event.stage_name = stage.name
                event.parallel_group = stage.name
                event.branch_index = idx
                event.metadata = {
                    **(event.metadata or {}),
                    "workflow_key": workflow.key,
                    "workflow_run_id": run_id,
                    "step_name": step.display_name(),
                    "step_agent": step.agent_key,
                    "stage_name": stage.name,
                    "parallel_group": stage.name,
                    "branch_index": idx,
                }
                if step_metadata is None and isinstance(event.metadata, dict):
                    step_metadata = event.metadata
                if event.response_text:
                    last_text = event.response_text
                if event.text_delta:
                    text_buffer.append(event.text_delta)
                if event.structured_output is not None:
                    last_structured = event.structured_output
                await queue.put(event)
                if event.is_terminal:
                    break

            if not last_text and text_buffer:
                last_text = "".join(text_buffer)

            chosen_output = None
            if last_structured is not None:
                chosen_output = last_structured
            elif last_text is not None:
                chosen_output = last_text

            validate_against_schema(
                step.output_schema,
                chosen_output,
                label=f"step '{step.display_name()}' output",
            )

            response = AgentRunResult(
                final_output=chosen_output,
                response_text=last_text
                if last_text is not None
                else (
                    json.dumps(last_structured, ensure_ascii=False)
                    if last_structured is not None
                    else None
                ),
                structured_output=last_structured,
                response_id=getattr(stream_handle, "last_response_id", None),
                usage=getattr(stream_handle, "usage", None),
                metadata=step_metadata,
            )
            branch_results.append(
                (
                    idx,
                    WorkflowStepResult(
                        name=step.display_name(),
                        agent_key=step.agent_key,
                        response=response,
                        stage_name=stage.name,
                        parallel_group=stage.name,
                        branch_index=idx,
                        output_schema=schema_to_json_schema(step.output_schema),
                    ),
                )
            )
        except Exception as exc:  # pragma: no cover - error funnel tested via runner
            await queue.put(("error", idx, exc))
        finally:
            await queue.put(("done", idx))

    tasks = [asyncio.create_task(_consume_branch(spec)) for spec in branch_specs]
    active = len(tasks)

    while active > 0:
        item = await queue.get()
        if isinstance(item, AgentStreamEvent):
            yield item
        elif isinstance(item, tuple) and item:
            tag = item[0]
            if tag == "done":
                active -= 1
            elif tag == "error":
                _, _branch_idx, exc = item
                for task in tasks:
                    if not task.done():
                        task.cancel()
                raise exc

    await asyncio.gather(*tasks)

    outputs: list[Any] = []
    for idx, step_result in sorted(branch_results, key=lambda x: x[0]):
        outputs.append(step_result.response.final_output)
        await recorder.step_end(
            run_id,
            sequence_no=len(prior_steps),
            step_name=step_result.name,
            step_agent=step_result.agent_key,
            response=step_result.response,
            status="succeeded",
            stage_name=stage.name,
            parallel_group=stage.name,
            branch_index=idx,
        )
        prior_steps.append(step_result)

    merged_output = await apply_reducer(stage.reducer, outputs, prior_steps)
    stage_state["next_input"] = merged_output

    post_items = await session_getter()
    delta_items = post_items[len(pre_items) :] if post_items else []

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
            step_result.agent_key,
            _response_model(step_result.response),
            getattr(step_result.response, "response_id", None),
        )
        for idx, step_result in sorted(branch_results, key=lambda x: x[0])
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


def _response_model(response: AgentRunResult | None) -> str | None:
    if response is None:
        return None
    metadata = getattr(response, "metadata", None)
    if isinstance(metadata, dict):
        model = metadata.get("model")
        return str(model) if model is not None else None
    return None


__all__ = ["stream_parallel_stage", "stream_sequential_stage"]
