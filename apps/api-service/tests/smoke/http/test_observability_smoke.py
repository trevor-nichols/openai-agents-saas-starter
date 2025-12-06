from __future__ import annotations

import httpx
import pytest

from tests.smoke.http.auth import auth_headers
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_logs_ingest(http_client: httpx.AsyncClient, smoke_state: SmokeState) -> None:
    resp = await http_client.post(
        "/api/v1/logs",
        json={
            "event": "smoke.log",
            "level": "info",
            "message": "smoke test log",
            "fields": {"suite": "http-smoke"},
        },
        headers=auth_headers(smoke_state),
    )
    assert resp.status_code == 202, resp.text
