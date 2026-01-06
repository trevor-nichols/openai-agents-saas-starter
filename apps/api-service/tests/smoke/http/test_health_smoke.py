from __future__ import annotations

import pytest
import httpx


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_health_and_ready(http_client: httpx.AsyncClient) -> None:
    health = await http_client.get("/health")
    assert health.status_code == 200
    body = health.json()
    assert body.get("status") == "healthy"

    ready = await http_client.get("/health/ready")
    assert ready.status_code == 200
    ready_body = ready.json()
    assert ready_body.get("status") == "ready"


async def test_storage_health(http_client: httpx.AsyncClient) -> None:
    health = await http_client.get("/health/storage")
    assert health.status_code == 200
    body = health.json()
    assert body.get("status") == "healthy"
