from __future__ import annotations

import httpx
import pytest

from tests.smoke.http.auth import auth_headers
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


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
