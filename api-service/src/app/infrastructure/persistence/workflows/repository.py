from __future__ import annotations

from typing import Any

from sqlalchemy import select, update

from app.domain.workflows import WorkflowRun, WorkflowRunRepository, WorkflowRunStep
from app.infrastructure.persistence.workflows.models import WorkflowRunModel, WorkflowRunStepModel


class SqlAlchemyWorkflowRunRepository(WorkflowRunRepository):
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def create_run(self, run: WorkflowRun) -> None:
        async with self._session_factory() as session:
            session.add(
                WorkflowRunModel(
                    id=run.id,
                    workflow_key=run.workflow_key,
                    tenant_id=run.tenant_id,
                    user_id=run.user_id,
                    status=run.status,
                    started_at=run.started_at,
                    ended_at=run.ended_at,
                    final_output_text=run.final_output_text,
                    final_output_structured=run.final_output_structured,
                    trace_id=run.trace_id,
                    request_message=run.request_message,
                    conversation_id=run.conversation_id,
                    metadata_json=run.metadata,
                )
            )
            await session.commit()

    async def update_run(self, run_id: str, **fields: Any) -> None:
        async with self._session_factory() as session:
            await session.execute(
                update(WorkflowRunModel).where(WorkflowRunModel.id == run_id).values(**fields)
            )
            await session.commit()

    async def create_step(self, step: WorkflowRunStep) -> None:
        async with self._session_factory() as session:
            session.add(
                WorkflowRunStepModel(
                    id=step.id,
                    workflow_run_id=step.workflow_run_id,
                    sequence_no=step.sequence_no,
                    step_name=step.step_name,
                    step_agent=step.step_agent,
                    status=step.status,
                    started_at=step.started_at,
                    ended_at=step.ended_at,
                    response_id=step.response_id,
                    response_text=step.response_text,
                    structured_output=step.structured_output,
                    raw_payload=step.raw_payload,
                    usage_input_tokens=step.usage_input_tokens,
                    usage_output_tokens=step.usage_output_tokens,
                )
            )
            await session.commit()

    async def update_step(self, step_id: str, **fields: Any) -> None:
        async with self._session_factory() as session:
            await session.execute(
                update(WorkflowRunStepModel)
                .where(WorkflowRunStepModel.id == step_id)
                .values(**fields)
            )
            await session.commit()

    async def get_run_with_steps(self, run_id: str) -> tuple[WorkflowRun, list[WorkflowRunStep]]:
        async with self._session_factory() as session:
            run_row = await session.scalar(
                select(WorkflowRunModel).where(WorkflowRunModel.id == run_id)
            )
            if run_row is None:
                raise ValueError(f"Workflow run '{run_id}' not found")

            step_rows = (
                await session.execute(
                    select(WorkflowRunStepModel)
                    .where(WorkflowRunStepModel.workflow_run_id == run_id)
                    .order_by(WorkflowRunStepModel.sequence_no)
                )
            ).scalars().all()

        run = WorkflowRun(
            id=run_row.id,
            workflow_key=run_row.workflow_key,
            tenant_id=run_row.tenant_id,
            user_id=run_row.user_id,
            status=run_row.status,
            started_at=run_row.started_at,
            ended_at=run_row.ended_at,
            final_output_text=run_row.final_output_text,
            final_output_structured=run_row.final_output_structured,
            trace_id=run_row.trace_id,
            request_message=run_row.request_message,
            conversation_id=run_row.conversation_id,
            metadata=run_row.metadata_json if hasattr(run_row, "metadata_json") else None,
        )

        steps = [
            WorkflowRunStep(
                id=row.id,
                workflow_run_id=row.workflow_run_id,
                sequence_no=row.sequence_no,
                step_name=row.step_name,
                step_agent=row.step_agent,
                status=row.status,
                started_at=row.started_at,
                ended_at=row.ended_at,
                response_id=row.response_id,
                response_text=row.response_text,
                structured_output=row.structured_output,
                raw_payload=row.raw_payload,
                usage_input_tokens=row.usage_input_tokens,
                usage_output_tokens=row.usage_output_tokens,
            )
            for row in step_rows
        ]

        return run, steps


__all__ = ["SqlAlchemyWorkflowRunRepository"]
