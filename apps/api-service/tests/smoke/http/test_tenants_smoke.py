from __future__ import annotations

from uuid import uuid4

import httpx
import pytest

from tests.smoke.http.auth import auth_headers, bearer_headers, login_for_tokens
from tests.smoke.http.config import SmokeConfig
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


async def test_tenant_members_and_invites(
    http_client: httpx.AsyncClient, smoke_state: SmokeState
) -> None:
    headers = auth_headers(smoke_state, tenant_role="owner")

    policy = await http_client.get("/api/v1/tenants/invites/policy", headers=headers)
    assert policy.status_code == 200, policy.text
    policy_body = policy.json()
    assert policy_body.get("default_expires_hours", 0) > 0
    assert policy_body.get("max_expires_hours", 0) >= policy_body.get(
        "default_expires_hours", 0
    )

    members = await http_client.get("/api/v1/tenants/members", headers=headers)
    assert members.status_code == 200, members.text
    members_body = members.json()
    assert isinstance(members_body.get("members"), list)
    assert (members_body.get("total") or 0) >= 1
    assert (members_body.get("owner_count") or 0) >= 1

    invite_email = f"smoke-team-{uuid4().hex[:8]}@example.com"
    issue = await http_client.post(
        "/api/v1/tenants/invites",
        json={"invited_email": invite_email, "role": "member"},
        headers=headers,
    )
    assert issue.status_code == 201, issue.text
    issue_body = issue.json()
    invite_id = issue_body.get("id")
    assert invite_id
    assert issue_body.get("invited_email") == invite_email
    assert issue_body.get("status") == "active"
    assert issue_body.get("invite_token")

    listing = await http_client.get(
        "/api/v1/tenants/invites",
        params={"email": invite_email},
        headers=headers,
    )
    assert listing.status_code == 200, listing.text
    listing_body = listing.json()
    invites = listing_body.get("invites") or []
    assert any(invite.get("id") == invite_id for invite in invites)

    revoke = await http_client.post(
        f"/api/v1/tenants/invites/{invite_id}/revoke",
        headers=headers,
    )
    assert revoke.status_code == 200, revoke.text
    revoke_body = revoke.json()
    assert revoke_body.get("status") == "revoked"
    assert revoke_body.get("revoked_reason") == "tenant_admin_action"


async def test_tenant_account_self_service(
    http_client: httpx.AsyncClient, smoke_state: SmokeState
) -> None:
    headers = auth_headers(smoke_state, tenant_role="owner")

    current = await http_client.get("/api/v1/tenants/account", headers=headers)
    assert current.status_code == 200, current.text
    body = current.json()
    assert body.get("id") == smoke_state.tenant_id

    updated = await http_client.patch(
        "/api/v1/tenants/account",
        json={"name": body.get("name", "Starter Tenant")},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    updated_body = updated.json()
    assert updated_body.get("id") == smoke_state.tenant_id


async def test_platform_tenant_crud_and_lifecycle(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_state: SmokeState,
) -> None:
    operator_tokens = await login_for_tokens(
        http_client,
        smoke_config,
        smoke_state.tenant_id,
        email=smoke_config.operator_email,
    )
    operator_headers = bearer_headers(operator_tokens["access_token"])

    list_resp = await http_client.get("/api/v1/platform/tenants", headers=operator_headers)
    assert list_resp.status_code == 200, list_resp.text

    suffix = uuid4().hex[:8]
    create_payload = {"name": f"Smoke Platform {suffix}", "slug": f"smoke-{suffix}"}
    created = await http_client.post(
        "/api/v1/platform/tenants",
        json=create_payload,
        headers=operator_headers,
    )
    assert created.status_code == 201, created.text
    created_body = created.json()
    tenant_id = created_body.get("id")
    assert tenant_id

    updated = await http_client.patch(
        f"/api/v1/platform/tenants/{tenant_id}",
        json={"name": f"Smoke Platform Updated {suffix}"},
        headers=operator_headers,
    )
    assert updated.status_code == 200, updated.text

    suspend = await http_client.post(
        f"/api/v1/platform/tenants/{tenant_id}/suspend",
        json={"reason": "smoke-test"},
        headers=operator_headers,
    )
    assert suspend.status_code == 200, suspend.text
    assert suspend.json().get("status") == "suspended"

    reactivate = await http_client.post(
        f"/api/v1/platform/tenants/{tenant_id}/reactivate",
        json={"reason": "smoke-test"},
        headers=operator_headers,
    )
    assert reactivate.status_code == 200, reactivate.text
    assert reactivate.json().get("status") == "active"

    if not smoke_config.enable_billing:
        deprovision = await http_client.post(
            f"/api/v1/platform/tenants/{tenant_id}/deprovision",
            json={"reason": "smoke-test"},
            headers=operator_headers,
        )
        assert deprovision.status_code == 200, deprovision.text
        assert deprovision.json().get("status") == "deprovisioned"
