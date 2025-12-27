from __future__ import annotations

import uuid

import httpx
import pytest

from tests.smoke.http.auth import auth_headers
from tests.smoke.http.config import SmokeConfig
from tests.smoke.http.helpers import delete_if_exists, require_enabled
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_container_lifecycle_and_binding(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_state: SmokeState,
) -> None:
    require_enabled(smoke_config.enable_containers, reason="SMOKE_ENABLE_CONTAINERS not enabled")

    headers = auth_headers(smoke_state, tenant_role="owner")
    container_id: str | None = None

    try:
        name = f"smoke-container-{uuid.uuid4().hex[:8]}"
        create = await http_client.post(
            "/api/v1/containers",
            json={"name": name, "memory_limit": "1g"},
            headers=headers,
        )
        assert create.status_code == 201, create.text
        body = create.json()
        container_id = body.get("id")
        assert container_id
        assert body.get("openai_id")

        listing = await http_client.get("/api/v1/containers", headers=headers)
        assert listing.status_code == 200, listing.text
        items = listing.json().get("items", [])
        assert isinstance(items, list)

        detail = await http_client.get(f"/api/v1/containers/{container_id}", headers=headers)
        assert detail.status_code == 200, detail.text
        detail_body = detail.json()
        assert detail_body.get("id") == container_id

        bind = await http_client.post(
            "/api/v1/containers/agents/triage/container",
            json={"container_id": container_id},
            headers=headers,
        )
        assert bind.status_code == 204, bind.text

        unbind = await http_client.delete(
            "/api/v1/containers/agents/triage/container",
            headers=headers,
        )
        assert unbind.status_code == 204, unbind.text
    finally:
        if container_id:
            await delete_if_exists(
                http_client,
                f"/api/v1/containers/{container_id}",
                headers=headers,
                expected_statuses=(204, 404),
            )
