from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.workflows import WorkflowRun, WorkflowRunStep, WorkflowStatus
from app.infrastructure.persistence.models.base import Base as ModelBase
from app.infrastructure.persistence.workflows.repository import (
    SqlAlchemyWorkflowRunRepository,
)


@pytest.fixture()
async def repo(tmp_path):
    db_path = tmp_path / "workflow_repo.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(ModelBase.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return SqlAlchemyWorkflowRunRepository(session_factory)


def _run(
    *,
    run_id: str,
    workflow_key: str,
    tenant_id: str,
    status: WorkflowStatus,
    started_at: datetime,
    ended_at: datetime | None = None,
    conversation_id: str | None = None,
) -> WorkflowRun:
    return WorkflowRun(
        id=run_id,
        workflow_key=workflow_key,
        tenant_id=tenant_id,
        user_id="user-1",
        status=status,
        started_at=started_at,
        ended_at=ended_at,
        final_output_text="done",
        final_output_structured=None,
        trace_id=None,
        request_message="hello",
        conversation_id=conversation_id,
        metadata=None,
    )


def _step(run_id: str, started_at: datetime, seq: int = 0) -> WorkflowRunStep:
    return WorkflowRunStep(
        id=f"step-{run_id}-{seq}",
        workflow_run_id=run_id,
        sequence_no=seq,
        step_name="step",
        step_agent="agent",
        status="succeeded",
        started_at=started_at,
        ended_at=started_at,
        response_id=None,
        response_text="hi",
        structured_output=None,
        raw_payload=None,
        usage_input_tokens=None,
        usage_output_tokens=None,
        stage_name=None,
        parallel_group=None,
        branch_index=None,
    )


@pytest.mark.anyio
async def test_list_runs_paginates_and_filters(repo):
    tenant_a = "tenant-a"
    tenant_b = "tenant-b"
    base = datetime.now(tz=UTC)

    runs = [
        _run(
            run_id="run-1",
            workflow_key="alpha",
            tenant_id=tenant_a,
            status=cast(WorkflowStatus, "succeeded"),
            started_at=base - timedelta(minutes=1),
            ended_at=base,
            conversation_id="conv-1",
        ),
        _run(
            run_id="run-2",
            workflow_key="alpha",
            tenant_id=tenant_a,
            status=cast(WorkflowStatus, "running"),
            started_at=base - timedelta(minutes=2),
            conversation_id="conv-2",
        ),
        _run(
            run_id="run-3",
            workflow_key="beta",
            tenant_id=tenant_a,
            status=cast(WorkflowStatus, "failed"),
            started_at=base - timedelta(minutes=3),
        ),
        _run(
            run_id="run-other",
            workflow_key="alpha",
            tenant_id=tenant_b,
            status=cast(WorkflowStatus, "succeeded"),
            started_at=base - timedelta(minutes=4),
        ),
    ]
    for run in runs:
        await repo.create_run(run)
        await repo.create_step(_step(run.id, run.started_at))

    page1 = await repo.list_runs(tenant_id=tenant_a, limit=2)
    assert len(page1.items) == 2
    assert page1.items[0].id == "run-1"  # newest first
    assert page1.next_cursor is not None

    page2 = await repo.list_runs(tenant_id=tenant_a, cursor=page1.next_cursor, limit=2)
    assert [item.id for item in page2.items] == ["run-2", "run-3"]
    assert page2.next_cursor is None

    filtered = await repo.list_runs(
        tenant_id=tenant_a, workflow_key="alpha", status="running", limit=5
    )
    assert [item.id for item in filtered.items] == ["run-2"]

    by_conversation = await repo.list_runs(
        tenant_id=tenant_a, conversation_id="conv-1", limit=5
    )
    assert [item.id for item in by_conversation.items] == ["run-1"]

    assert all(item.step_count == 1 for item in page1.items)
    assert page1.items[0].duration_ms is not None


@pytest.mark.anyio
async def test_list_runs_respects_started_filters(repo):
    tenant_id = "tenant-a"
    now = datetime.now(tz=UTC)
    earlier = now - timedelta(hours=1)

    await repo.create_run(
        _run(
            run_id="r-new",
            workflow_key="alpha",
            tenant_id=tenant_id,
            status=cast(WorkflowStatus, "running"),
            started_at=now,
        )
    )
    await repo.create_run(
        _run(
            run_id="r-old",
            workflow_key="alpha",
            tenant_id=tenant_id,
            status=cast(WorkflowStatus, "running"),
            started_at=earlier,
        )
    )

    after_filter = await repo.list_runs(tenant_id=tenant_id, started_after=now - timedelta(minutes=1))
    assert [item.id for item in after_filter.items] == ["r-new"]

    before_filter = await repo.list_runs(tenant_id=tenant_id, started_before=earlier + timedelta(seconds=1))
    assert [item.id for item in before_filter.items] == ["r-old"]


@pytest.mark.anyio
async def test_soft_delete_hides_run_and_steps(repo):
    tenant_id = "tenant-a"
    now = datetime.now(tz=UTC)
    run = _run(
        run_id="run-del",
        workflow_key="alpha",
        tenant_id=tenant_id,
        status=cast(WorkflowStatus, "succeeded"),
        started_at=now,
    )
    step = _step(run.id, run.started_at)
    await repo.create_run(run)
    await repo.create_step(step)

    await repo.soft_delete_run(run.id, tenant_id=tenant_id, deleted_by="user-1", reason="cleanup")

    with pytest.raises(ValueError):
        await repo.get_run_with_steps(run.id)

    page = await repo.list_runs(tenant_id=tenant_id)
    assert not page.items

    run_row, steps = await repo.get_run_with_steps(run.id, include_deleted=True)
    assert run_row.deleted_at is not None
    assert steps[0].deleted_at is not None
    assert steps[0].deleted_reason == "cleanup"


@pytest.mark.anyio
async def test_hard_delete_removes_run(repo):
    tenant_id = "tenant-a"
    now = datetime.now(tz=UTC)
    run = _run(
        run_id="run-hard",
        workflow_key="alpha",
        tenant_id=tenant_id,
        status=cast(WorkflowStatus, "succeeded"),
        started_at=now,
    )
    await repo.create_run(run)

    await repo.hard_delete_run(run.id, tenant_id=tenant_id)

    with pytest.raises(ValueError):
        await repo.get_run_with_steps(run.id, include_deleted=True)
