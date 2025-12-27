from __future__ import annotations

import httpx
import pytest

from tests.smoke.http.auth import auth_headers
from tests.smoke.http.config import SmokeConfig
from tests.smoke.http.helpers import require_enabled
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_service_account_issue_and_tokens(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_state: SmokeState,
) -> None:
    require_enabled(
        smoke_config.enable_service_accounts,
        reason="SMOKE_ENABLE_SERVICE_ACCOUNTS not enabled",
    )

    issue_resp = await http_client.post(
        "/api/v1/auth/service-accounts/issue",
        json={
            "account": "analytics-batch",
            "scopes": ["conversations:read"],
            "tenant_id": smoke_state.tenant_id,
            "fingerprint": "smoke-suite",
            "force": True,
        },
        headers={"Authorization": "Bearer dev-demo"},
    )
    assert issue_resp.status_code == 201, issue_resp.text
    issue_body = issue_resp.json()
    assert issue_body.get("refresh_token")

    browser_issue = await http_client.post(
        "/api/v1/auth/service-accounts/browser-issue",
        json={
            "account": "analytics-batch",
            "scopes": ["conversations:read"],
            "tenant_id": smoke_state.tenant_id,
            "fingerprint": "smoke-suite-browser",
            "force": True,
            "reason": "Smoke test browser issuance",
        },
        headers=auth_headers(smoke_state),
    )
    assert browser_issue.status_code == 201, browser_issue.text
    browser_body = browser_issue.json()
    assert browser_body.get("refresh_token")

    list_resp = await http_client.get(
        "/api/v1/auth/service-accounts/tokens",
        params={"account": "analytics-batch", "limit": 50},
        headers=auth_headers(smoke_state),
    )
    assert list_resp.status_code == 200, list_resp.text
    items = list_resp.json().get("items", [])
    assert isinstance(items, list) and items

    target = next(
        (item for item in items if item.get("account") == "analytics-batch"), None
    )
    assert target and target.get("jti")

    revoke_resp = await http_client.post(
        f"/api/v1/auth/service-accounts/tokens/{target['jti']}/revoke",
        json={"reason": "smoke revoke"},
        headers=auth_headers(smoke_state),
    )
    assert revoke_resp.status_code == 200, revoke_resp.text
