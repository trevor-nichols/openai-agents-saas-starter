from __future__ import annotations

import httpx
import pytest

from tests.smoke.http.auth import auth_headers
from tests.smoke.http.config import SmokeConfig
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]
async def test_billing_plans_and_subscription(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_state: SmokeState,
) -> None:
    if not smoke_config.enable_billing:
        pytest.skip("SMOKE_ENABLE_BILLING not enabled")

    headers = auth_headers(smoke_state, tenant_role="owner")

    plans = await http_client.get("/api/v1/billing/plans", headers=headers)
    assert plans.status_code == 200, plans.text
    catalog = plans.json()
    assert isinstance(catalog, list)
    assert any(plan.get("code") for plan in catalog)

    sub = await http_client.get(
        f"/api/v1/billing/tenants/{smoke_state.tenant_id}/subscription", headers=headers
    )
    assert sub.status_code == 200, sub.text
    body = sub.json()
    assert body.get("tenant_id") == smoke_state.tenant_id
