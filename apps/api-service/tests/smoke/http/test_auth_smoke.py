from __future__ import annotations

import httpx
import pytest

from tests.smoke.http.auth import auth_headers, login_for_tokens
from tests.smoke.http.config import SmokeConfig
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_login_and_refresh(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_state: SmokeState,
) -> None:
    # Already logged in via fixture, but verify refresh flow end-to-end.
    tokens = await login_for_tokens(http_client, smoke_config, smoke_state.tenant_id)

    assert tokens["access_token"]
    assert tokens["refresh_token"]
    assert tokens["kid"]
    assert tokens["refresh_kid"]

    refresh_resp = await http_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_resp.status_code == 200
    refreshed = refresh_resp.json()
    assert refreshed["access_token"]
    assert refreshed["refresh_token"]
    assert refreshed["user_id"] == tokens.get("user_id")


async def test_me_endpoint_returns_current_user(
    http_client: httpx.AsyncClient, smoke_state: SmokeState
) -> None:
    resp = await http_client.get("/api/v1/auth/me", headers=auth_headers(smoke_state))
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("user_id") == smoke_state.user_id
