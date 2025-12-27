from __future__ import annotations

import httpx
import pytest


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_status_snapshot_and_rss(http_client: httpx.AsyncClient) -> None:
    snapshot = await http_client.get("/api/v1/status")
    assert snapshot.status_code == 200
    body = snapshot.json()
    assert isinstance(body.get("overview"), dict)
    assert isinstance(body.get("incidents"), list)
    assert isinstance(body.get("services"), list)

    rss = await http_client.get("/api/v1/status/rss")
    assert rss.status_code == 200
    assert "<rss" in rss.text
