"""Workflow runner that sequences agents deterministically (with optional parallel stages)."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Callable, Sequence
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

from agents import trace

from app.domain.ai import AgentRunResult, RunOptions
from app.domain.ai.models import AgentStreamEvent
from app.domain.workflows import WorkflowRun, WorkflowRunRepository, WorkflowRunStep
from app.services.agents.context import ConversationActorContext
from app.services.agents.interaction_context import InteractionContextBuilder
from app.services.agents.provider_registry import AgentProviderRegistry, get_provider_registry
from app.workflows.registry import WorkflowRegistry
from app.workflows.specs import WorkflowSpec, WorkflowStage, WorkflowStep


@dataclass(slots=True)
class WorkflowStepResult:
    name: str
    agent_key: str
    response: AgentRunResult
    stage_name: str | None = None
    parallel_group: str | None = None
    branch_index: int | None = None


@dataclass(slots=True)
class WorkflowRunResult:
    workflow_key: str
    workflow_run_id: str
    conversation_id: str
    steps: list[WorkflowStepResult]
    final_output: Any | None = None


class WorkflowRunner:
    def __init__(
        self,
        *,
        registry: WorkflowRegistry,
        provider_registry: AgentProviderRegistry | None = None,
        interaction_builder: InteractionContextBuilder | None = None,
        run_repository: WorkflowRunRepository | None = None,
        cancellation_tracker: set[str] | None = None,
    ) -> None:
        self._registry = registry
        self._provider_registry = provider_registry or get_provider_registry()
        self._interaction_builder = interaction_builder or InteractionContextBuilder()
        self._run_repository = run_repository
        self._cancellations = cancellation_tracker or set()

    async def run(
        self,
        workflow: WorkflowSpec,
        *,
        actor: ConversationActorContext,
        message: str,
        conversation_id: str,
        location: Any | None = None,
        share_location: bool | None = None,
    ) -> WorkflowRunResult:
        provider = self._provider_registry.get_default()
        run_id = _uuid()
        await self._record_run_start(
            run_id,
            workflow,
            actor=actor,
            message=message,
            conversation_id=conversation_id,
        )
        runtime_ctx = await self._interaction_builder.build(
            actor=actor,
            request=_WorkflowRequestProxy(
                message=message,
                location=location,
                share_location=share_location,
            ),
            conversation_id=conversation_id,
        )

        current_input: Any = message
        steps_results: list[WorkflowStepResult] = []
        stages = workflow.resolved_stages()

        try:
            with trace(workflow_name=workflow.key, group_id=conversation_id):
                for _stage_index, stage in enumerate(stages):
                    self._raise_if_cancelled(run_id)
                    if stage.mode == "parallel":
                        current_input = await self._run_parallel_stage(
                            run_id,
                            workflow,
                            stage,
                            current_input,
                            steps_results,
                            provider,
                            runtime_ctx,
                            conversation_id,
                        )
                    else:
                        current_input = await self._run_sequential_stage(
                            run_id,
                            workflow,
                            stage,
                            current_input,
                            steps_results,
                            provider,
                            runtime_ctx,
                            conversation_id,
                        )

            await self._record_run_end(
                run_id,
                status="succeeded",
                final_output=current_input if steps_results else None,
            )
        except _WorkflowCancelled:
            await self._record_run_end(run_id, status="cancelled", final_output=None)
            raise
        except Exception:
            await self._record_run_end(run_id, status="failed", final_output=None)
            raise

        return WorkflowRunResult(
            workflow_key=workflow.key,
            workflow_run_id=run_id,
            conversation_id=conversation_id,
            steps=steps_results,
            final_output=current_input if steps_results else None,
        )

    async def run_stream(
        self,
        workflow: WorkflowSpec,
        *,
        actor: ConversationActorContext,
        message: str,
        conversation_id: str,
        location: Any | None = None,
        share_location: bool | None = None,
    ) -> AsyncIterator[AgentStreamEvent]:
        provider = self._provider_registry.get_default()
        run_id = _uuid()
        await self._record_run_start(
            run_id,
            workflow,
            actor=actor,
            message=message,
            conversation_id=conversation_id,
        )
        runtime_ctx = await self._interaction_builder.build(
            actor=actor,
            request=_WorkflowRequestProxy(
                message=message,
                location=location,
                share_location=share_location,
            ),
            conversation_id=conversation_id,
        )

        current_input: Any = message
        prior_steps: list[WorkflowStepResult] = []
        stages = workflow.resolved_stages()

        try:
            with trace(workflow_name=workflow.key, group_id=conversation_id):
                for _stage_index, stage in enumerate(stages):
                    self._raise_if_cancelled(run_id)
                    if stage.mode == "parallel":
                        stage_state: dict[str, Any] = {}
                        async for event in self._stream_parallel_stage(
                            run_id,
                            workflow,
                            stage,
                            current_input,
                            prior_steps,
                            provider,
                            runtime_ctx,
                            conversation_id,
                            stage_state,
                        ):
                            yield event
                        current_input = stage_state.get(
                            "next_input",
                            prior_steps[-1].response.final_output if prior_steps else current_input,
                        )
                    else:
                        self._raise_if_cancelled(run_id)
                        async for event in self._stream_sequential_stage(
                            run_id,
                            workflow,
                            stage,
                            current_input,
                            prior_steps,
                            provider,
                            runtime_ctx,
                            conversation_id,
                        ):
                            yield event
                        if prior_steps:
                            current_input = prior_steps[-1].response.final_output

            await self._record_run_end(
                run_id,
                status="succeeded",
                final_output=current_input if prior_steps else None,
            )
        except _WorkflowCancelled:
            await self._record_run_end(run_id, status="cancelled", final_output=None)
            # Emit terminal lifecycle event so stream consumers learn about cancellation.
            yield AgentStreamEvent(
                kind="lifecycle",
                is_terminal=True,
                metadata={
                    "workflow_key": workflow.key,
                    "workflow_run_id": run_id,
                    "state": "cancelled",
                },
            )
        except Exception:
            await self._record_run_end(run_id, status="failed", final_output=None)
            raise


    async def _evaluate_guard(
        self, dotted_path: str, current_input: Any, prior_steps: Sequence[WorkflowStepResult]
    ) -> bool:
        func = _import_callable(dotted_path, "guard")
        value = func(current_input, prior_steps)
        if asyncio.iscoroutine(value):
            value = await value
        return bool(value)

    async def _apply_reducer(
        self,
        reducer_path: str | None,
        outputs: list[Any],
        prior_steps: Sequence[WorkflowStepResult],
    ) -> Any:
        if reducer_path is None:
            if len(outputs) == 1:
                return outputs[0]
            return outputs
        func = _import_callable(reducer_path, "reducer")
        value = func(outputs, prior_steps)
        if asyncio.iscoroutine(value):
            value = await value
        return value

    async def _run_sequential_stage(
        self,
        run_id: str,
        workflow: WorkflowSpec,
        stage: WorkflowStage,
        current_input: Any,
        steps_results: list[WorkflowStepResult],
        provider,
        runtime_ctx,
        conversation_id: str,
    ) -> Any:
        for step in stage.steps:
            self._raise_if_cancelled(run_id)
            if step.guard and not await self._evaluate_guard(
                step.guard, current_input, steps_results
            ):
                continue

            step_input = current_input
            if step.input_mapper:
                step_input = await self._run_mapper(step.input_mapper, current_input, steps_results)

            options = RunOptions(max_turns=step.max_turns) if step.max_turns is not None else None
            metadata = {
                "prompt_runtime_ctx": runtime_ctx,
                "workflow_key": workflow.key,
                "workflow_run_id": run_id,
                "stage_name": stage.name,
            }
            chosen_output, response = await self._execute_agent_step(
                step,
                step_input,
                provider,
                runtime_ctx,
                conversation_id,
                metadata,
                options,
            )

            await self._record_step_end(
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
                )
            )
            current_input = response.final_output
        return current_input

    async def _run_parallel_stage(
        self,
        run_id: str,
        workflow: WorkflowSpec,
        stage: WorkflowStage,
        current_input: Any,
        steps_results: list[WorkflowStepResult],
        provider,
        runtime_ctx,
        conversation_id: str,
    ) -> Any:
        branch_specs: list[tuple[int, WorkflowStep, Any, RunOptions | None, dict[str, Any]]] = []
        for idx, step in enumerate(stage.steps):
            self._raise_if_cancelled(run_id)
            if step.guard and not await self._evaluate_guard(
                step.guard, current_input, steps_results
            ):
                continue
            step_input = current_input
            if step.input_mapper:
                step_input = await self._run_mapper(step.input_mapper, current_input, steps_results)
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
            return idx, step, await self._execute_agent_step(
                step,
                step_input,
                provider,
                runtime_ctx,
                conversation_id,
                metadata,
                options,
            )

        branch_results = await asyncio.gather(*[_run_branch(spec) for spec in branch_specs])

        outputs: list[Any] = []
        for idx, step, (chosen_output, response) in sorted(branch_results, key=lambda x: x[0]):
            outputs.append(chosen_output)
            await self._record_step_end(
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
                )
            )

        next_input = await self._apply_reducer(stage.reducer, outputs, steps_results)
        return next_input

    async def _execute_agent_step(
        self,
        step: WorkflowStep,
        step_input: Any,
        provider,
        runtime_ctx,
        conversation_id: str,
        metadata: dict[str, Any],
        options: RunOptions | None,
    ) -> tuple[Any | None, AgentRunResult]:
        result = await provider.runtime.run(
            step.agent_key,
            step_input,
            conversation_id=conversation_id,
            metadata=metadata,
            options=options,
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
        return chosen_output, response

    async def _stream_sequential_stage(
        self,
        run_id: str,
        workflow: WorkflowSpec,
        stage: WorkflowStage,
        current_input: Any,
        prior_steps: list[WorkflowStepResult],
        provider,
        runtime_ctx,
        conversation_id: str,
    ) -> AsyncIterator[AgentStreamEvent]:
        for step in stage.steps:
            self._raise_if_cancelled(run_id)
            if step.guard and not await self._evaluate_guard(
                step.guard, current_input, prior_steps
            ):
                continue

            step_input = current_input
            if step.input_mapper:
                step_input = await self._run_mapper(step.input_mapper, current_input, prior_steps)

            options = RunOptions(max_turns=step.max_turns) if step.max_turns is not None else None
            metadata = {
                "prompt_runtime_ctx": runtime_ctx,
                "workflow_key": workflow.key,
                "workflow_run_id": run_id,
                "stage_name": stage.name,
            }
            stream_handle = provider.runtime.run_stream(
                step.agent_key,
                step_input,
                conversation_id=conversation_id,
                metadata=metadata,
                options=options,
            )

            last_text: str | None = None
            text_buffer: list[str] = []
            last_structured: Any | None = None
            step_metadata = getattr(stream_handle, "metadata", None)
            async for event in stream_handle.events():
                self._raise_if_cancelled(run_id)
                event.conversation_id = conversation_id
                event.agent = event.agent or step.agent_key
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

            prior_steps.append(
                WorkflowStepResult(
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
                )
            )
            await self._record_step_end(
                run_id,
                sequence_no=len(prior_steps) - 1,
                step_name=step.display_name(),
                step_agent=step.agent_key,
                response=prior_steps[-1].response,
                status="succeeded",
                stage_name=stage.name,
                parallel_group=None,
                branch_index=None,
            )
            if chosen_output is not None:
                current_input = chosen_output

    async def _stream_parallel_stage(
        self,
        run_id: str,
        workflow: WorkflowSpec,
        stage: WorkflowStage,
        current_input: Any,
        prior_steps: list[WorkflowStepResult],
        provider,
        runtime_ctx,
        conversation_id: str,
        stage_state: dict[str, Any],
    ) -> AsyncIterator[AgentStreamEvent]:
        branch_specs: list[tuple[int, WorkflowStep, Any, RunOptions | None, dict[str, Any]]] = []
        for idx, step in enumerate(stage.steps):
            self._raise_if_cancelled(run_id)
            if step.guard and not await self._evaluate_guard(
                step.guard, current_input, prior_steps
            ):
                continue
            step_input = current_input
            if step.input_mapper:
                step_input = await self._run_mapper(step.input_mapper, current_input, prior_steps)
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
            # No branches executed; carry forward existing input.
            stage_state["next_input"] = current_input
            return

        queue: asyncio.Queue[Any] = asyncio.Queue()
        branch_results: list[tuple[int, WorkflowStepResult]] = []

        async def _consume_branch(
            spec: tuple[int, WorkflowStep, Any, RunOptions | None, dict[str, Any]]
        ):
            idx, step, step_input, options, metadata = spec
            try:
                stream_handle = provider.runtime.run_stream(
                    step.agent_key,
                    step_input,
                    conversation_id=conversation_id,
                    metadata=metadata,
                    options=options,
                )
                last_text: str | None = None
                text_buffer: list[str] = []
                last_structured: Any | None = None
                step_metadata = getattr(stream_handle, "metadata", None)
                async for event in stream_handle.events():
                    self._raise_if_cancelled(run_id)
                    event.conversation_id = conversation_id
                    event.agent = event.agent or step.agent_key
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
                        ),
                    )
                )
            except Exception as exc:
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
                    _, branch_idx, exc = item
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    raise exc

        await asyncio.gather(*tasks)

        outputs: list[Any] = []
        for idx, step_result in sorted(branch_results, key=lambda x: x[0]):
            outputs.append(step_result.response.final_output)
            await self._record_step_end(
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

        merged_output = await self._apply_reducer(stage.reducer, outputs, prior_steps)
        stage_state["next_input"] = merged_output

    async def _run_mapper(
        self, dotted_path: str, current_input: Any, prior_steps: Sequence[WorkflowStepResult]
    ) -> Any:
        func = _import_callable(dotted_path, "input_mapper")
        value = func(current_input, prior_steps)
        if asyncio.iscoroutine(value):
            value = await value
        return value

    async def _record_run_start(
        self,
        run_id: str,
        workflow: WorkflowSpec,
        *,
        actor: ConversationActorContext,
        message: str,
        conversation_id: str,
    ) -> None:
        if not self._run_repository:
            return
        await self._run_repository.create_run(
            WorkflowRun(
                id=run_id,
                workflow_key=workflow.key,
                tenant_id=actor.tenant_id,
                user_id=actor.user_id,
                status="running",
                started_at=_now(),
                request_message=message,
                conversation_id=conversation_id,
                metadata=None,
                final_output_structured=None,
                final_output_text=None,
                trace_id=None,
                ended_at=None,
            )
        )

    async def _record_step_end(
        self,
        run_id: str,
        *,
        sequence_no: int,
        step_name: str,
        step_agent: str,
        response: AgentRunResult,
        status: str,
        stage_name: str | None,
        parallel_group: str | None,
        branch_index: int | None,
    ) -> None:
        if not self._run_repository:
            return
        raw_payload = response.metadata if isinstance(response.metadata, dict) else None
        await self._run_repository.create_step(
            WorkflowRunStep(
                id=_uuid(),
                workflow_run_id=run_id,
                sequence_no=sequence_no,
                step_name=step_name,
                step_agent=step_agent,
                status=status,  # type: ignore[arg-type]
                started_at=_now(),
                ended_at=_now(),
                response_id=response.response_id,
                response_text=response.response_text,
                structured_output=response.structured_output,
                raw_payload=raw_payload,
                usage_input_tokens=getattr(response.usage, "input_tokens", None),
                usage_output_tokens=getattr(response.usage, "output_tokens", None),
                stage_name=stage_name,
                parallel_group=parallel_group,
                branch_index=branch_index,
            )
        )

    async def _record_run_end(
        self,
        run_id: str,
        *,
        status: str,
        final_output: Any,
    ) -> None:
        if not self._run_repository:
            return
        await self._run_repository.update_run(
            run_id,
            status=status,
            ended_at=_now(),
            final_output_text=str(final_output) if final_output is not None else None,
            final_output_structured=final_output if not isinstance(final_output, str) else None,
        )

    def flag_cancel(self, run_id: str) -> None:
        self._cancellations.add(run_id)

    def _raise_if_cancelled(self, run_id: str) -> None:
        if run_id in self._cancellations:
            raise _WorkflowCancelled()


def _import_callable(path: str, label: str) -> Callable[..., Any]:
    if ":" in path:
        module_path, attr = path.split(":", 1)
    elif "." in path:
        module_path, attr = path.rsplit(".", 1)
    else:
        raise ValueError(f"Invalid dotted path for {label}: {path}")
    module = __import__(module_path, fromlist=[attr])
    func = getattr(module, attr, None)
    if func is None or not callable(func):
        raise ValueError(f"{label} '{path}' must be a callable")
    return func


def _uuid() -> str:
    return str(uuid4())


def _now():
    import datetime

    return datetime.datetime.now(tz=datetime.UTC)


class _WorkflowRequestProxy(SimpleNamespace):
    """Tiny adapter so InteractionContextBuilder can reuse its shape expectations."""

    def __init__(self, *, message: str, location: Any | None, share_location: bool | None):
        super().__init__(message=message, location=location, share_location=share_location)


class _WorkflowCancelled(Exception):
    """Internal marker exception for cooperative cancellation."""


__all__ = [
    "WorkflowRunner",
    "WorkflowRunResult",
    "WorkflowStepResult",
]
