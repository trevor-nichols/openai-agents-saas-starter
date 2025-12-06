from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.workflows.recording import WorkflowRunRecorder


class _FakeWorkflowRepo:
    def __init__(self) -> None:
        self.updated: list[tuple[str, dict[str, object]]] = []

    async def create_run(self, *_args, **_kwargs):
        return None

    async def update_run(self, run_id: str, **fields):
        self.updated.append((run_id, fields))

    async def create_step(self, *_args, **_kwargs):
        return None


@pytest.mark.asyncio
async def test_workflow_completion_status_is_normalized(monkeypatch):
    repo = _FakeWorkflowRepo()
    recorder = WorkflowRunRecorder(repository=repo)
    actor = SimpleNamespace(tenant_id="tenant-1", user_id="user-1")

    calls: list[dict[str, object]] = []

    async def _record(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr("app.services.workflows.recording.activity_service.record", _record)

    await recorder.end(
        "run-1",
        status="cancelled",
        final_output=None,
        actor=actor,
        workflow_key="analysis",
    )

    assert calls, "activity_service.record should be invoked"
    assert calls[0]["action"] == "workflow.run.cancelled"
    assert calls[0]["status"] == "pending"
    assert calls[0]["metadata"]["workflow_key"] == "analysis"
    assert "status" not in calls[0]["metadata"]
    # Repository still receives original status for accuracy
    assert repo.updated[0][1]["status"] == "cancelled"
