from __future__ import annotations

import httpx
import pytest

from tests.smoke.http.auth import auth_headers


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_feature_snapshot(
    http_client: httpx.AsyncClient, smoke_state
) -> None:
    response = await http_client.get(
        "/api/v1/features",
        headers=auth_headers(smoke_state),
    )
    assert response.status_code == 200
    body = response.json()
    assert "billing_enabled" in body
    assert "billing_stream_enabled" in body
