from __future__ import annotations

import uuid

import httpx
import pytest

from tests.smoke.http.auth import auth_headers
from tests.smoke.http.config import SmokeConfig
from tests.smoke.http.helpers import delete_if_exists, require_enabled
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_vector_store_create_list_search_delete(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_state: SmokeState,
) -> None:
    require_enabled(smoke_config.enable_vector, reason="SMOKE_ENABLE_VECTOR not enabled")

    headers = auth_headers(smoke_state, tenant_role="owner")
    store_id: str | None = None

    try:
        name = f"smoke-vector-{uuid.uuid4().hex[:8]}"
        create = await http_client.post(
            "/api/v1/vector-stores",
            json={"name": name, "description": "smoke"},
            headers=headers,
        )
        assert create.status_code == 201, create.text
        store = create.json()
        store_id = store.get("id")
        assert store_id
        assert store.get("openai_id")

        listing = await http_client.get("/api/v1/vector-stores", headers=headers)
        assert listing.status_code == 200, listing.text
        items = listing.json().get("items", [])
        assert isinstance(items, list)

        detail = await http_client.get(f"/api/v1/vector-stores/{store_id}", headers=headers)
        assert detail.status_code == 200, detail.text
        detail_body = detail.json()
        assert detail_body.get("id") == store_id

        search = await http_client.post(
            f"/api/v1/vector-stores/{store_id}/search",
            json={"query": "smoke"},
            headers=headers,
        )
        assert search.status_code == 200, search.text
        search_body = search.json()
        assert search_body.get("object")
        assert isinstance(search_body.get("data", []), list)
    finally:
        if store_id:
            await delete_if_exists(
                http_client,
                f"/api/v1/vector-stores/{store_id}",
                headers=headers,
                expected_statuses=(204, 404),
            )
