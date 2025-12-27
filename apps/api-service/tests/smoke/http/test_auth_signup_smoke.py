from __future__ import annotations

from typing import Any
from uuid import uuid4

import httpx
import pytest

from tests.smoke.http.auth import bearer_headers, login_for_tokens
from tests.smoke.http.config import SmokeConfig
from tests.smoke.http.helpers import require_enabled


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}@example.com"


def _strong_password(label: str) -> str:
    suffix = uuid4().hex[:8]
    return f"{label}-{suffix}!Aa9"


async def test_signup_requests_invites_and_register(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_seed: dict[str, Any],
) -> None:
    require_enabled(smoke_config.enable_auth_signup, reason="SMOKE_ENABLE_AUTH_SIGNUP not enabled")

    policy_resp = await http_client.get("/api/v1/auth/signup-policy")
    assert policy_resp.status_code == 200, policy_resp.text
    policy_body = policy_resp.json()
    policy = policy_body.get("policy")
    assert policy in {"public", "invite_only", "approval"}

    tenant_entry = smoke_seed["tenants"][smoke_config.tenant_slug]
    tenant_id = tenant_entry["tenant_id"]
    operator_tokens = await login_for_tokens(
        http_client,
        smoke_config,
        tenant_id,
        email=smoke_config.operator_email,
    )
    operator_headers = bearer_headers(operator_tokens["access_token"])

    approve_email = _unique_email("smoke-approve")
    reject_email = _unique_email("smoke-reject")
    for email in (approve_email, reject_email):
        access_resp = await http_client.post(
            "/api/v1/auth/request-access",
            json={
                "email": email,
                "organization": "Smoke Test Org",
                "full_name": "Smoke Request",
                "message": "Smoke signup request",
                "accept_terms": True,
            },
        )
        assert access_resp.status_code == 202, access_resp.text

    list_resp = await http_client.get(
        "/api/v1/auth/signup-requests",
        params={"status": "pending", "limit": 200},
        headers=operator_headers,
    )
    assert list_resp.status_code == 200, list_resp.text
    requests = list_resp.json().get("requests", [])

    approve_req = next((item for item in requests if item.get("email") == approve_email), None)
    reject_req = next((item for item in requests if item.get("email") == reject_email), None)
    assert approve_req and reject_req

    approve_resp = await http_client.post(
        f"/api/v1/auth/signup-requests/{approve_req['id']}/approve",
        json={},
        headers=operator_headers,
    )
    assert approve_resp.status_code == 200, approve_resp.text
    approve_body = approve_resp.json()
    invite_token = (
        approve_body.get("invite", {}).get("invite_token")
        if isinstance(approve_body.get("invite"), dict)
        else None
    )
    assert invite_token

    reject_resp = await http_client.post(
        f"/api/v1/auth/signup-requests/{reject_req['id']}/reject",
        json={"reason": "Smoke test reject"},
        headers=operator_headers,
    )
    assert reject_resp.status_code == 200, reject_resp.text

    issued_email = _unique_email("smoke-invite")
    invite_issue = await http_client.post(
        "/api/v1/auth/invites",
        json={"invited_email": issued_email},
        headers=operator_headers,
    )
    assert invite_issue.status_code == 201, invite_issue.text
    invite_body = invite_issue.json()
    invite_id = invite_body.get("id")
    assert invite_id

    invite_list = await http_client.get(
        "/api/v1/auth/invites",
        params={"limit": 50},
        headers=operator_headers,
    )
    assert invite_list.status_code == 200, invite_list.text
    invites = invite_list.json().get("invites", [])
    assert any(item.get("id") == invite_id for item in invites)

    revoke_resp = await http_client.post(
        f"/api/v1/auth/invites/{invite_id}/revoke",
        headers=operator_headers,
    )
    assert revoke_resp.status_code == 200, revoke_resp.text

    register_payload = {
        "email": _unique_email("smoke-register"),
        "password": _strong_password("SmokeSignup"),
        "tenant_name": f"Smoke Signup {uuid4().hex[:6]}",
        "accept_terms": True,
    }
    if policy != "public":
        register_payload["invite_token"] = invite_token

    register_resp = await http_client.post("/api/v1/auth/register", json=register_payload)
    assert register_resp.status_code == 201, register_resp.text
    register_body = register_resp.json()
    assert register_body.get("tenant_slug")
    assert register_body.get("access_token")
