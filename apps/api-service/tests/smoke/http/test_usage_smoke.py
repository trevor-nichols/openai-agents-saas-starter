from __future__ import annotations

import httpx
import pytest

from tests.smoke.http.auth import auth_headers
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_usage_counters(http_client: httpx.AsyncClient, smoke_state: SmokeState) -> None:
    resp = await http_client.get("/api/v1/usage", headers=auth_headers(smoke_state))
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert body, "Expected at least one seeded usage counter"
    assert any((item.get("requests") or 0) >= 1 for item in body)
