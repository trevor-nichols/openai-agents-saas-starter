from __future__ import annotations

import httpx
import pytest

from tests.smoke.http.auth import auth_headers
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_user_profile(http_client: httpx.AsyncClient, smoke_state: SmokeState) -> None:
    resp = await http_client.get("/api/v1/users/me", headers=auth_headers(smoke_state))
    assert resp.status_code == 200
    body = resp.json()
    data = body.get("data") or {}
    assert data.get("user_id") == smoke_state.user_id


async def test_user_consents(http_client: httpx.AsyncClient, smoke_state: SmokeState) -> None:
    payload = {"policy_key": "terms-of-service", "version": "v1"}
    record = await http_client.post(
        "/api/v1/users/consents",
        json=payload,
        headers=auth_headers(smoke_state),
    )
    assert record.status_code == 201, record.text

    resp = await http_client.get("/api/v1/users/consents", headers=auth_headers(smoke_state))
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert any(
        item.get("policy_key") == payload["policy_key"]
        and item.get("version") == payload["version"]
        for item in body
    )


async def test_notification_preferences(
    http_client: httpx.AsyncClient, smoke_state: SmokeState
) -> None:
    payload = {"channel": "email", "category": "product_updates", "enabled": True}
    upsert = await http_client.put(
        "/api/v1/users/notification-preferences",
        json=payload,
        headers=auth_headers(smoke_state),
    )
    assert upsert.status_code == 200, upsert.text
    body = upsert.json()
    assert body.get("channel") == payload["channel"]
    assert body.get("category") == payload["category"]

    listing = await http_client.get(
        "/api/v1/users/notification-preferences",
        headers=auth_headers(smoke_state),
    )
    assert listing.status_code == 200
    items = listing.json()
    assert isinstance(items, list)
    assert any(
        item.get("channel") == payload["channel"]
        and item.get("category") == payload["category"]
        for item in items
    )
