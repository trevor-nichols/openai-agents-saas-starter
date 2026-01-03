from __future__ import annotations

import httpx
import pytest

from tests.smoke.http.auth import bearer_headers, login_for_tokens
from tests.smoke.http.config import SmokeConfig
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_platform_tenants_list_and_get(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_state: SmokeState,
) -> None:
    tokens = await login_for_tokens(
        http_client,
        smoke_config,
        smoke_state.tenant_id,
        email=smoke_config.operator_email,
    )
    headers = bearer_headers(tokens["access_token"])

    listing = await http_client.get("/api/v1/platform/tenants?limit=10", headers=headers)
    assert listing.status_code == 200, listing.text
    body = listing.json()
    accounts = body.get("accounts")
    assert isinstance(accounts, list)
    assert any(
        account.get("id") == smoke_state.tenant_id
        or account.get("slug") == smoke_config.tenant_slug
        for account in accounts
    )

    detail = await http_client.get(
        f"/api/v1/platform/tenants/{smoke_state.tenant_id}",
        headers=headers,
    )
    assert detail.status_code == 200, detail.text
    detail_body = detail.json()
    assert detail_body.get("id") == smoke_state.tenant_id
    assert detail_body.get("slug") == smoke_config.tenant_slug
