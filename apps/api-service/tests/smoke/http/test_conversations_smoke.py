from __future__ import annotations

import uuid

import httpx
import pytest

from tests.smoke.http.auth import auth_headers
from tests.smoke.http.config import SmokeConfig
from tests.smoke.http.helpers import fetch_sse_event_json, require_enabled
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def _start_chat_stream(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_state: SmokeState,
) -> dict[str, str]:
    require_enabled(smoke_config.enable_ai, reason="SMOKE_ENABLE_AI not enabled")

    payload = {
        "message": "Hello",
        "agent_type": "triage",
    }
    event = await fetch_sse_event_json(
        http_client,
        "POST",
        "/api/v1/chat/stream",
        json=payload,
        headers=auth_headers(smoke_state),
        timeout_seconds=smoke_config.request_timeout,
    )
    conversation_id = event.get("conversation_id")
    assert isinstance(conversation_id, str) and conversation_id
    return {"conversation_id": conversation_id}


async def test_conversation_list_and_detail(
    http_client: httpx.AsyncClient, smoke_state: SmokeState
) -> None:
    headers = auth_headers(smoke_state)

    list_resp = await http_client.get("/api/v1/conversations", headers=headers)
    assert list_resp.status_code == 200
    items = list_resp.json().get("items", [])
    assert isinstance(items, list)

    # Use seeded conversation if available, else skip detail assertions.
    if smoke_state.conversation_id:
        detail = await http_client.get(
            f"/api/v1/conversations/{smoke_state.conversation_id}", headers=headers
        )
        assert detail.status_code == 200
        body = detail.json()
        assert body.get("conversation_id") == smoke_state.conversation_id


async def test_conversation_search_and_events(
    http_client: httpx.AsyncClient, smoke_state: SmokeState
) -> None:
    if not smoke_state.conversation_id:
        pytest.skip("No seeded conversation to search; ensure fixtures include one.")

    headers = auth_headers(smoke_state)
    search = await http_client.get(
        "/api/v1/conversations/search", params={"q": "hello"}, headers=headers
    )
    assert search.status_code == 200
    results = search.json().get("items", [])
    assert isinstance(results, list)

    events = await http_client.get(
        f"/api/v1/conversations/{smoke_state.conversation_id}/events",
        headers=headers,
    )
    assert events.status_code == 200
    ev_items = events.json().get("items", [])
    assert isinstance(ev_items, list)


async def test_conversation_delete_on_fresh_seed(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_state: SmokeState,
) -> None:
    # Apply a fresh conversation keyed uniquely, then delete it to keep suite idempotent.
    unique_key = f"delete-{uuid.uuid4()}"
    spec = {
        "tenants": [
            {
                "slug": smoke_config.tenant_slug,
                "name": smoke_config.tenant_name,
                "users": [],
                "conversations": [
                    {
                        "key": unique_key,
                        "status": "active",
                        "agent_entrypoint": "default",
                        "messages": [{"role": "user", "text": "temp"}],
                    }
                ],
            }
        ]
    }
    seed_resp = await http_client.post("/api/v1/test-fixtures/apply", json=spec)
    if seed_resp.status_code == 404:
        pytest.skip("Fixtures endpoint disabled; cannot seed deletable conversation.")
    assert seed_resp.status_code == 201, seed_resp.text
    convo_id = seed_resp.json()["tenants"][smoke_config.tenant_slug]["conversations"][
        unique_key
    ]["conversation_id"]

    delete = await http_client.delete(
        f"/api/v1/conversations/{convo_id}", headers=auth_headers(smoke_state)
    )
    assert delete.status_code == 204


async def test_conversation_ledger_events(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_state: SmokeState,
) -> None:
    session = await _start_chat_stream(http_client, smoke_config, smoke_state)
    conversation_id = session["conversation_id"]

    headers = auth_headers(smoke_state)
    resp = await http_client.get(
        f"/api/v1/conversations/{conversation_id}/ledger/events", headers=headers
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("conversation_id") == conversation_id
    items = body.get("items", [])
    assert isinstance(items, list)
    assert items


async def test_conversation_ledger_stream(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_state: SmokeState,
) -> None:
    session = await _start_chat_stream(http_client, smoke_config, smoke_state)
    conversation_id = session["conversation_id"]

    headers = auth_headers(smoke_state)
    event = await fetch_sse_event_json(
        http_client,
        "GET",
        f"/api/v1/conversations/{conversation_id}/ledger/stream",
        headers=headers,
        timeout_seconds=smoke_config.request_timeout,
    )
    assert event.get("schema") == "public_sse_v1"
    assert event.get("conversation_id") == conversation_id
