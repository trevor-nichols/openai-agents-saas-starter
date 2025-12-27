from __future__ import annotations

import httpx
import pytest

from tests.smoke.http.auth import auth_headers
from tests.smoke.http.config import SmokeConfig
from tests.smoke.http.helpers import fetch_sse_event_json, require_enabled
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_activity_list_and_receipts(
    http_client: httpx.AsyncClient,
    smoke_state: SmokeState,
) -> None:
    headers = auth_headers(smoke_state)

    resp = await http_client.get("/api/v1/activity", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    items = body.get("items", [])
    assert isinstance(items, list)
    assert items, "Expected activity list to include at least one event from login."

    event_id = items[0].get("id")
    assert isinstance(event_id, str) and event_id

    mark_read = await http_client.post(f"/api/v1/activity/{event_id}/read", headers=headers)
    assert mark_read.status_code == 200, mark_read.text
    mark_read_body = mark_read.json()
    assert isinstance(mark_read_body.get("unread_count"), int)

    dismiss = await http_client.post(f"/api/v1/activity/{event_id}/dismiss", headers=headers)
    assert dismiss.status_code == 200, dismiss.text
    dismiss_body = dismiss.json()
    assert isinstance(dismiss_body.get("unread_count"), int)

    mark_all = await http_client.post("/api/v1/activity/mark-all-read", headers=headers)
    assert mark_all.status_code == 200, mark_all.text
    mark_all_body = mark_all.json()
    assert mark_all_body.get("unread_count") == 0

    updated = await http_client.get("/api/v1/activity", headers=headers)
    assert updated.status_code == 200, updated.text
    updated_items = updated.json().get("items", [])
    assert isinstance(updated_items, list)
    matched = next((item for item in updated_items if item.get("id") == event_id), None)
    assert matched is not None
    assert matched.get("read_state") in {"read", "dismissed"}


async def test_activity_stream_handshake(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_state: SmokeState,
) -> None:
    require_enabled(
        smoke_config.enable_activity_stream,
        reason="SMOKE_ENABLE_ACTIVITY_STREAM not enabled",
    )

    event = await fetch_sse_event_json(
        http_client,
        "GET",
        "/api/v1/activity/stream",
        headers=auth_headers(smoke_state),
        timeout_seconds=smoke_config.request_timeout,
    )

    assert isinstance(event.get("id"), str)
    assert event.get("tenant_id") == smoke_state.tenant_id
    assert isinstance(event.get("action"), str) and event.get("action")
