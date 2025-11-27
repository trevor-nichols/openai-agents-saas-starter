from __future__ import annotations

import os
from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from datetime import datetime, UTC

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ENABLE_BILLING", "false")
os.environ.setdefault("ENABLE_USAGE_GUARDRAILS", "false")

pytestmark = pytest.mark.auto_migrations(enabled=True)

from app.api.dependencies.auth import require_current_user  # noqa: E402
from app.api.v1.workflows.schemas import StreamingWorkflowEvent  # noqa: E402
from app.domain.ai import AgentRunResult  # noqa: E402
from app.domain.ai.models import AgentStreamEvent  # noqa: E402
from app.domain.workflows import WorkflowRun, WorkflowRunStep  # noqa: E402
from app.services.workflows.runner import WorkflowStepResult, WorkflowRunResult  # noqa: E402
from app.services.workflows.service import get_workflow_service  # noqa: E402
from main import app  # noqa: E402

TEST_TENANT_ID = str(uuid4())


def _stub_current_user():
    return {
        "user_id": "test-user",
        "subject": "user:test-user",
        "payload": {
            "scope": "conversations:read conversations:write",
            "tenant_id": TEST_TENANT_ID,
            "roles": ["admin"],
        },
    }


@pytest.fixture(autouse=True)
def _override_current_user():
    previous = app.dependency_overrides.get(require_current_user)
    app.dependency_overrides[require_current_user] = _stub_current_user
    try:
        yield
    finally:
        if previous is None:
            app.dependency_overrides.pop(require_current_user, None)
        else:
            app.dependency_overrides[require_current_user] = previous


@pytest.fixture(scope="function")
def client(_configure_agent_provider):
    with TestClient(app) as test_client:
        yield test_client


def test_list_workflows(client: TestClient) -> None:
    response = client.get("/api/v1/workflows")
    assert response.status_code == 200
    payload = response.json()
    assert any(wf["key"] == "triage_pipeline" for wf in payload)


@patch("app.services.workflows.service.WorkflowService.run_workflow", new_callable=AsyncMock)
def test_run_workflow_sync(mock_run_workflow: AsyncMock, client: TestClient) -> None:
    mock_run_workflow.return_value = WorkflowRunResult(
        workflow_key="triage_pipeline",
        workflow_run_id="run-1",
        conversation_id="conv-1",
        steps=[
            WorkflowStepResult(
                name="triage",
                agent_key="triage",
                response=AgentRunResult(final_output="hi", response_text="hi"),
            )
        ],
    )

    response = client.post(
        "/api/v1/workflows/triage_pipeline/run",
        json={"message": "hello"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["workflow_key"] == "triage_pipeline"
    assert data["workflow_run_id"] == "run-1"
    assert data["steps"][0]["agent_key"] == "triage"


@patch("app.services.workflows.service.WorkflowService.run_workflow_stream", new_callable=AsyncMock)
def test_run_workflow_stream(mock_run_stream: AsyncMock, client: TestClient) -> None:
    async def _gen():
        yield AgentStreamEvent(
            kind="run_item",
            response_id="r1",
            text_delta="hello",
            metadata={
                "workflow_key": "triage_pipeline",
                "workflow_run_id": "run-1",
                "step_name": "triage",
                "step_agent": "triage",
            },
            is_terminal=False,
        )
        yield AgentStreamEvent(
            kind="run_item",
            response_id="r1",
            response_text="done",
            metadata={
                "workflow_key": "triage_pipeline",
                "workflow_run_id": "run-1",
                "step_name": "triage",
                "step_agent": "triage",
            },
            is_terminal=True,
        )

    mock_run_stream.return_value = _gen()

    events: list[StreamingWorkflowEvent] = []
    with client.stream(
        "POST", "/api/v1/workflows/triage_pipeline/run-stream", json={"message": "hello"}
    ) as response:
        assert response.status_code == 200
        for line in response.iter_lines():
            if not line:
                continue
            text = line if isinstance(line, str) else str(line)
            if text.startswith("data: "):
                payload = StreamingWorkflowEvent.model_validate_json(text[6:])
                events.append(payload)
                if payload.is_terminal:
                    break

    assert events
    assert events[-1].workflow_key == "triage_pipeline"
    assert events[-1].workflow_run_id == "run-1"


def test_get_workflow_run(client: TestClient) -> None:
    service = get_workflow_service()
    repo = getattr(service._runner, "_run_repository", None)
    assert repo is not None

    run = WorkflowRun(
        id="run-abc",
        workflow_key="triage_pipeline",
        tenant_id=TEST_TENANT_ID,
        user_id="test-user",
        status="succeeded",
        started_at=datetime.now(tz=UTC),
        ended_at=datetime.now(tz=UTC),
        final_output_text="done",
        final_output_structured=None,
        trace_id=None,
        request_message="hello",
        conversation_id=None,
        metadata=None,
    )
    step = WorkflowRunStep(
        id="step-1",
        workflow_run_id="run-abc",
        sequence_no=0,
        step_name="triage",
        step_agent="triage",
        status="succeeded",
        started_at=datetime.now(tz=UTC),
        ended_at=datetime.now(tz=UTC),
        response_id="r1",
        response_text="done",
        structured_output=None,
        raw_payload=None,
        usage_input_tokens=None,
        usage_output_tokens=None,
    )

    import anyio

    anyio.run(repo.create_run, run)
    anyio.run(repo.create_step, step)

    response = client.get(f"/api/v1/workflows/runs/{run.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["workflow_run_id"] == run.id
    assert body["steps"][0]["agent_key"] == "triage"


@pytest.mark.auto_migrations(enabled=True)
def test_get_workflow_run_via_db(client: TestClient, _provider_engine) -> None:
    # Create a real run/step in the DB using the SQLAlchemy repo
    from app.infrastructure.persistence.workflows.repository import (
        SqlAlchemyWorkflowRunRepository,
    )

    repo = SqlAlchemyWorkflowRunRepository(lambda: _provider_engine.begin().__aenter__())

    run_id = "run-db"
    run = WorkflowRun(
        id=run_id,
        workflow_key="triage_pipeline",
        tenant_id=TEST_TENANT_ID,
        user_id="test-user",
        status="succeeded",
        started_at=datetime.now(tz=UTC),
        ended_at=datetime.now(tz=UTC),
        final_output_text="done",
        final_output_structured=None,
        trace_id=None,
        request_message="hi",
        conversation_id=None,
        metadata=None,
    )
    step = WorkflowRunStep(
        id="step-db",
        workflow_run_id=run_id,
        sequence_no=0,
        step_name="triage",
        step_agent="triage",
        status="succeeded",
        started_at=datetime.now(tz=UTC),
        ended_at=datetime.now(tz=UTC),
        response_id="resp-db",
        response_text="done",
        structured_output=None,
        raw_payload=None,
        usage_input_tokens=None,
        usage_output_tokens=None,
    )

    import anyio

    anyio.run(repo.create_run, run)
    anyio.run(repo.create_step, step)

    response = client.get(f"/api/v1/workflows/runs/{run_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["workflow_run_id"] == run_id
    assert body["steps"][0]["agent_key"] == "triage"
