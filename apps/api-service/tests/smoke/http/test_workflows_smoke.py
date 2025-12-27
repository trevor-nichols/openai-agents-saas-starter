from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
import pytest

from tests.smoke.http.auth import auth_headers, login_for_tokens
from tests.smoke.http.config import SmokeConfig
from tests.smoke.http.helpers import assert_status_in, fetch_sse_event_json, require_enabled
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


@dataclass(frozen=True)
class WorkflowStreamSession:
    workflow_key: str
    workflow_run_id: str
    conversation_id: str
    event: dict[str, Any]


def _select_workflow_key(items: list[dict[str, Any]]) -> str:
    for item in items:
        if item.get("key") == "analysis_code":
            return item["key"]
    for item in items:
        if item.get("default"):
            return item["key"]
    if not items:
        pytest.skip("No workflows available to exercise.")
    return items[0]["key"]


async def _resolve_workflow_key(
    client: httpx.AsyncClient, headers: dict[str, str]
) -> str:
    catalog = await client.get("/api/v1/workflows", headers=headers)
    assert catalog.status_code == 200, catalog.text
    items = catalog.json().get("items", [])
    assert isinstance(items, list)
    return _select_workflow_key(items)


def _workflow_run_predicate(event: dict[str, Any]) -> bool:
    workflow = event.get("workflow")
    if not isinstance(workflow, dict):
        return False
    run_id = workflow.get("workflow_run_id")
    return isinstance(run_id, str) and bool(run_id)


@pytest.fixture(scope="module")
async def workflow_stream_run(
    smoke_config: SmokeConfig, smoke_seed: dict[str, Any]
) -> WorkflowStreamSession:
    require_enabled(smoke_config.enable_ai, reason="SMOKE_ENABLE_AI not enabled")

    tenant_entry = smoke_seed["tenants"][smoke_config.tenant_slug]
    tenant_id = tenant_entry["tenant_id"]

    async with httpx.AsyncClient(
        base_url=smoke_config.base_url,
        timeout=smoke_config.request_timeout,
    ) as client:
        tokens = await login_for_tokens(client, smoke_config, tenant_id)
        headers = {
            "Authorization": f"Bearer {tokens['access_token']}",
            "X-Tenant-Id": tenant_id,
            "X-Tenant-Role": "owner",
        }
        workflow_key = await _resolve_workflow_key(client, headers)
        event = await fetch_sse_event_json(
            client,
            "POST",
            f"/api/v1/workflows/{workflow_key}/run-stream",
            json={"message": "Hello from smoke"},
            headers=headers,
            predicate=_workflow_run_predicate,
            timeout_seconds=smoke_config.request_timeout,
        )

    assert event.get("schema") == "public_sse_v1"
    conversation_id = event.get("conversation_id")
    assert isinstance(conversation_id, str) and conversation_id
    workflow = event.get("workflow")
    assert isinstance(workflow, dict)
    workflow_run_id = workflow.get("workflow_run_id")
    assert isinstance(workflow_run_id, str) and workflow_run_id
    return WorkflowStreamSession(
        workflow_key=workflow_key,
        workflow_run_id=workflow_run_id,
        conversation_id=conversation_id,
        event=event,
    )


async def test_workflows_list_and_runs(http_client: httpx.AsyncClient, smoke_state: SmokeState):
    headers = auth_headers(smoke_state, tenant_role="viewer")

    catalog = await http_client.get("/api/v1/workflows", headers=headers)
    assert catalog.status_code == 200
    workflows = catalog.json()
    assert "items" in workflows
    assert isinstance(workflows.get("items"), list)

    runs = await http_client.get("/api/v1/workflows/runs", headers=headers)
    assert runs.status_code == 200
    body = runs.json()
    assert "items" in body
    assert isinstance(body.get("items"), list)


async def test_workflow_descriptor(
    http_client: httpx.AsyncClient,
    smoke_state: SmokeState,
) -> None:
    headers = auth_headers(smoke_state, tenant_role="viewer")
    workflow_key = await _resolve_workflow_key(http_client, headers)

    resp = await http_client.get(f"/api/v1/workflows/{workflow_key}", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("key") == workflow_key
    assert isinstance(body.get("stages"), list)


async def test_workflow_run_stream_handshake(
    workflow_stream_run: WorkflowStreamSession,
) -> None:
    workflow = workflow_stream_run.event.get("workflow", {})
    assert workflow.get("workflow_key") == workflow_stream_run.workflow_key
    assert workflow.get("workflow_run_id") == workflow_stream_run.workflow_run_id


async def test_workflow_run_detail(
    http_client: httpx.AsyncClient,
    smoke_state: SmokeState,
    workflow_stream_run: WorkflowStreamSession,
) -> None:
    resp = await http_client.get(
        f"/api/v1/workflows/runs/{workflow_stream_run.workflow_run_id}",
        headers=auth_headers(smoke_state, tenant_role="viewer"),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("workflow_run_id") == workflow_stream_run.workflow_run_id
    assert body.get("workflow_key") == workflow_stream_run.workflow_key


async def test_workflow_run_cancel(
    http_client: httpx.AsyncClient,
    smoke_state: SmokeState,
    workflow_stream_run: WorkflowStreamSession,
) -> None:
    resp = await http_client.post(
        f"/api/v1/workflows/runs/{workflow_stream_run.workflow_run_id}/cancel",
        headers=auth_headers(smoke_state, tenant_role="viewer"),
    )
    assert_status_in(resp, (202, 409))
    if resp.status_code == 202:
        body = resp.json()
        assert body.get("workflow_run_id") == workflow_stream_run.workflow_run_id
        assert body.get("success") is True


async def test_workflow_run_replay_events(
    http_client: httpx.AsyncClient,
    smoke_state: SmokeState,
    workflow_stream_run: WorkflowStreamSession,
) -> None:
    resp = await http_client.get(
        f"/api/v1/workflows/runs/{workflow_stream_run.workflow_run_id}/replay/events",
        headers=auth_headers(smoke_state, tenant_role="viewer"),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("workflow_run_id") == workflow_stream_run.workflow_run_id
    assert body.get("conversation_id") == workflow_stream_run.conversation_id
    items = body.get("items", [])
    assert isinstance(items, list)
    assert items


async def test_workflow_run_replay_stream(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_state: SmokeState,
    workflow_stream_run: WorkflowStreamSession,
) -> None:
    event = await fetch_sse_event_json(
        http_client,
        "GET",
        f"/api/v1/workflows/runs/{workflow_stream_run.workflow_run_id}/replay/stream",
        headers=auth_headers(smoke_state, tenant_role="viewer"),
        predicate=_workflow_run_predicate,
        timeout_seconds=smoke_config.request_timeout,
    )
    assert event.get("schema") == "public_sse_v1"
    assert event.get("conversation_id") == workflow_stream_run.conversation_id
    workflow = event.get("workflow", {})
    assert workflow.get("workflow_run_id") == workflow_stream_run.workflow_run_id
