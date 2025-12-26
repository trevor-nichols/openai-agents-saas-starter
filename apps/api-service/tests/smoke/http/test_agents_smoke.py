from __future__ import annotations

import httpx
import pytest

from tests.smoke.http.auth import auth_headers
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_agents_catalog_and_status(
    http_client: httpx.AsyncClient, smoke_state: SmokeState
) -> None:
    headers = auth_headers(smoke_state)
    catalog = await http_client.get("/api/v1/agents", headers=headers)
    assert catalog.status_code == 200
    body = catalog.json()
    assert isinstance(body, dict)
    agents = body.get("items", [])
    assert any(agent.get("name") == "triage" for agent in agents)

    status = await http_client.get("/api/v1/agents/triage/status", headers=headers)
    assert status.status_code == 200
    body = status.json()
    assert body.get("name") == "triage"
    assert body.get("status") == "active"
