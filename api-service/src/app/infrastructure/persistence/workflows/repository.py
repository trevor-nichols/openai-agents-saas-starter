from __future__ import annotations

import base64
import json
from datetime import datetime
from typing import Any, cast

from sqlalchemy import and_, func, or_, select, update

from app.domain.workflows import (
    WorkflowRun,
    WorkflowRunListItem,
    WorkflowRunListPage,
    WorkflowRunRepository,
    WorkflowRunStep,
    WorkflowStatus,
)
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
                    stage_name=step.stage_name,
                    parallel_group=step.parallel_group,
                    branch_index=step.branch_index,
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
                stage_name=getattr(row, "stage_name", None),
                parallel_group=getattr(row, "parallel_group", None),
                branch_index=getattr(row, "branch_index", None),
            )
            for row in step_rows
        ]

        return run, steps

    async def list_runs(
        self,
        *,
        tenant_id: str,
        workflow_key: str | None = None,
        status: WorkflowStatus | None = None,
        started_before: datetime | None = None,
        started_after: datetime | None = None,
        conversation_id: str | None = None,
        cursor: str | None = None,
        limit: int = 20,
    ) -> WorkflowRunListPage:
        safe_limit = max(1, min(limit, 100))
        cursor_filter = _decode_cursor(cursor) if cursor else None

        async with self._session_factory() as session:
            stmt = select(WorkflowRunModel).where(WorkflowRunModel.tenant_id == tenant_id)

            if workflow_key:
                stmt = stmt.where(WorkflowRunModel.workflow_key == workflow_key)
            if status:
                stmt = stmt.where(WorkflowRunModel.status == status)
            if conversation_id:
                stmt = stmt.where(WorkflowRunModel.conversation_id == conversation_id)
            if started_after:
                stmt = stmt.where(WorkflowRunModel.started_at >= started_after)
            if started_before:
                stmt = stmt.where(WorkflowRunModel.started_at <= started_before)
            if cursor_filter:
                started_at_cursor, id_cursor = cursor_filter
                stmt = stmt.where(
                    or_(
                        WorkflowRunModel.started_at < started_at_cursor,
                        and_(
                            WorkflowRunModel.started_at == started_at_cursor,
                            WorkflowRunModel.id < id_cursor,
                        ),
                    )
                )

            stmt = stmt.order_by(WorkflowRunModel.started_at.desc(), WorkflowRunModel.id.desc())
            stmt = stmt.limit(safe_limit + 1)

            run_rows = (await session.execute(stmt)).scalars().all()

            run_ids = [row.id for row in run_rows[:safe_limit]]
            step_counts: dict[str, int] = {}
            if run_ids:
                counts = await session.execute(
                    select(
                        WorkflowRunStepModel.workflow_run_id,
                        func.count().label("step_count"),
                    )
                    .where(WorkflowRunStepModel.workflow_run_id.in_(run_ids))
                    .group_by(WorkflowRunStepModel.workflow_run_id)
                )
                step_counts = {
                    row.workflow_run_id: int(row.step_count) for row in counts.all()
                }

        has_more = len(run_rows) > safe_limit
        visible_rows = run_rows[:safe_limit]
        next_cursor = None
        if has_more:
            tail = run_rows[safe_limit - 1]
            next_cursor = _encode_cursor(tail.started_at, tail.id)

        items = [
            WorkflowRunListItem(
                id=row.id,
                workflow_key=row.workflow_key,
                status=cast(WorkflowStatus, row.status),
                started_at=row.started_at,
                ended_at=row.ended_at,
                user_id=row.user_id,
                conversation_id=row.conversation_id,
                step_count=step_counts.get(row.id, 0),
                duration_ms=_duration_ms(row.started_at, row.ended_at),
                final_output_text=row.final_output_text,
            )
            for row in visible_rows
        ]

        return WorkflowRunListPage(items=items, next_cursor=next_cursor)

    async def cancel_run(self, run_id: str, *, ended_at: datetime) -> None:
        async with self._session_factory() as session:
            result = await session.execute(
                update(WorkflowRunModel)
                .where(WorkflowRunModel.id == run_id, WorkflowRunModel.status == "running")
                .values(status="cancelled", ended_at=ended_at)
            )
            if result.rowcount == 0:
                raise RuntimeError("Workflow run is not active")
            await session.commit()

    async def cancel_running_steps(self, run_id: str, *, ended_at: datetime) -> None:
        async with self._session_factory() as session:
            await session.execute(
                update(WorkflowRunStepModel)
                .where(
                    WorkflowRunStepModel.workflow_run_id == run_id,
                    WorkflowRunStepModel.status == "running",
                )
                .values(status="cancelled", ended_at=ended_at)
            )
            await session.commit()


__all__ = ["SqlAlchemyWorkflowRunRepository"]


def _encode_cursor(started_at: datetime, run_id: str) -> str:
    payload = {"started_at": started_at.isoformat(), "id": run_id}
    raw = json.dumps(payload).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def _decode_cursor(cursor: str) -> tuple[datetime, str]:
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8"))
        return datetime.fromisoformat(data["started_at"]), data["id"]
    except Exception as exc:  # pragma: no cover - invalid cursor input
        raise ValueError("Invalid pagination cursor") from exc


def _duration_ms(started_at: datetime | None, ended_at: datetime | None) -> int | None:
    if not started_at or not ended_at:
        return None
    delta = ended_at - started_at
    return int(delta.total_seconds() * 1000)
