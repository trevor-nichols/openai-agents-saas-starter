"""Workflow runner that sequences agents deterministically."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Callable, Sequence
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

from app.domain.ai import AgentRunResult, RunOptions
from app.domain.ai.models import AgentStreamEvent
from app.domain.workflows import WorkflowRun, WorkflowRunRepository, WorkflowRunStep
from app.services.agents.context import ConversationActorContext
from app.services.agents.interaction_context import InteractionContextBuilder
from app.services.agents.provider_registry import AgentProviderRegistry, get_provider_registry
from app.workflows.registry import WorkflowRegistry
from app.workflows.specs import WorkflowSpec


@dataclass(slots=True)
class WorkflowStepResult:
    name: str
    agent_key: str
    response: AgentRunResult


@dataclass(slots=True)
class WorkflowRunResult:
    workflow_key: str
    workflow_run_id: str
    conversation_id: str
    steps: list[WorkflowStepResult]

    @property
    def final_output(self) -> Any:
        return self.steps[-1].response.final_output if self.steps else None


class WorkflowRunner:
    def __init__(
        self,
        *,
        registry: WorkflowRegistry,
        provider_registry: AgentProviderRegistry | None = None,
        interaction_builder: InteractionContextBuilder | None = None,
        run_repository: WorkflowRunRepository | None = None,
    ) -> None:
        self._registry = registry
        self._provider_registry = provider_registry or get_provider_registry()
        self._interaction_builder = interaction_builder or InteractionContextBuilder()
        self._run_repository = run_repository

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
        try:
            for step in workflow.steps:
                if step.guard and not await self._evaluate_guard(
                    step.guard, current_input, steps_results
                ):
                    continue

                step_input = current_input
                if step.input_mapper:
                    step_input = await self._run_mapper(
                        step.input_mapper, current_input, steps_results
                    )

                options = (
                    RunOptions(max_turns=step.max_turns) if step.max_turns is not None else None
                )
                result = await provider.runtime.run(
                    step.agent_key,
                    step_input,
                    conversation_id=conversation_id,
                    metadata={"prompt_runtime_ctx": runtime_ctx},
                    options=options,
                )

                await self._record_step_end(
                    run_id,
                    sequence_no=len(steps_results),
                    step_name=step.display_name(),
                    step_agent=step.agent_key,
                    response=result,
                    status="succeeded",
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

                steps_results.append(
                    WorkflowStepResult(
                        name=step.display_name(),
                        agent_key=step.agent_key,
                        response=AgentRunResult(
                            final_output=chosen_output,
                            response_text=fallback_response_text,
                            structured_output=result.structured_output,
                            response_id=result.response_id,
                            usage=result.usage,
                            metadata=result.metadata,
                            tool_outputs=result.tool_outputs,
                        ),
                    )
                )
                current_input = chosen_output

            await self._record_run_end(
                run_id,
                status="succeeded",
                final_output=current_input,
            )
        except Exception:
            await self._record_run_end(run_id, status="failed", final_output=None)
            raise

        return WorkflowRunResult(
            workflow_key=workflow.key,
            workflow_run_id=run_id,
            conversation_id=conversation_id,
            steps=steps_results,
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

        try:
            for step in workflow.steps:
                if step.guard and not await self._evaluate_guard(
                    step.guard, current_input, prior_steps
                ):
                    continue

                step_input = current_input
                if step.input_mapper:
                    step_input = await self._run_mapper(
                        step.input_mapper, current_input, prior_steps
                    )

                options = (
                    RunOptions(max_turns=step.max_turns) if step.max_turns is not None else None
                )
                stream_handle = provider.runtime.run_stream(
                    step.agent_key,
                    step_input,
                    conversation_id=conversation_id,
                    metadata={"prompt_runtime_ctx": runtime_ctx},
                    options=options,
                )

                last_text: str | None = None
                text_buffer: list[str] = []
                last_structured: Any | None = None
                step_metadata = getattr(stream_handle, "metadata", None)
                async for event in stream_handle.events():
                    event.conversation_id = conversation_id
                    event.agent = event.agent or step.agent_key
                    event.metadata = {
                        **(event.metadata or {}),
                        "workflow_key": workflow.key,
                        "workflow_run_id": run_id,
                        "step_name": step.display_name(),
                        "step_agent": step.agent_key,
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

                if chosen_output is not None:
                    current_input = chosen_output
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
                    )
                )
                await self._record_step_end(
                    run_id,
                    sequence_no=len(prior_steps) - 1,
                    step_name=step.display_name(),
                    step_agent=step.agent_key,
                    response=prior_steps[-1].response,
                    status="succeeded",
                )

            await self._record_run_end(
                run_id,
                status="succeeded",
                final_output=current_input,
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


__all__ = [
    "WorkflowRunner",
    "WorkflowRunResult",
    "WorkflowStepResult",
]
