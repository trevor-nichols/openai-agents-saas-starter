from __future__ import annotations

import httpx
import pytest

from tests.smoke.http.auth import auth_headers
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_tenant_settings_roundtrip(
    http_client: httpx.AsyncClient, smoke_state: SmokeState
) -> None:
    headers = auth_headers(smoke_state, tenant_role="owner")

    current = await http_client.get("/api/v1/tenants/settings", headers=headers)
    assert current.status_code == 200
    body = current.json()
    assert body.get("tenant_id") == smoke_state.tenant_id

    payload = {
        "billing_contacts": body.get("billing_contacts", []),
        "billing_webhook_url": body.get("billing_webhook_url"),
        "plan_metadata": body.get("plan_metadata", {}),
        "flags": body.get("flags", {}),
    }
    updated = await http_client.put(
        "/api/v1/tenants/settings",
        json=payload,
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    updated_body = updated.json()
    assert updated_body.get("tenant_id") == smoke_state.tenant_id
