from __future__ import annotations

import uuid

import httpx
import pytest

from tests.smoke.http.auth import auth_headers
from tests.smoke.http.config import SmokeConfig
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


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
