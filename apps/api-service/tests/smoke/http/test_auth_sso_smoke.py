from __future__ import annotations

import httpx
import pytest

from tests.smoke.http.config import SmokeConfig
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_sso_provider_list_and_start(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_state: SmokeState,
) -> None:
    if not smoke_config.enable_auth_sso:
        pytest.skip("SSO smoke disabled; set SMOKE_ENABLE_AUTH_SSO=1 to enable.")

    provider = smoke_config.sso_provider

    provider_resp = await http_client.get(
        "/api/v1/auth/sso/providers",
        params={"tenant_id": smoke_state.tenant_id},
    )
    assert provider_resp.status_code == 200, provider_resp.text
    providers = provider_resp.json().get("providers", [])
    assert any(item.get("provider_key") == provider for item in providers)

    start_resp = await http_client.post(
        f"/api/v1/auth/sso/{provider}/start",
        json={"tenant_id": smoke_state.tenant_id},
    )
    assert start_resp.status_code == 200, start_resp.text
    authorize_url = start_resp.json().get("authorize_url")
    assert authorize_url
