from __future__ import annotations

from typing import Any
from uuid import uuid4

import httpx
import pytest

from tests.smoke.http.auth import auth_headers, bearer_headers, login_for_tokens
from tests.smoke.http.config import SmokeConfig
from tests.smoke.http.helpers import require_enabled
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


def _strong_password(label: str) -> str:
    suffix = uuid4().hex[:8]
    return f"{label}-{suffix}!Aa9"


async def test_email_verification_flow(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_seed: dict[str, Any],
) -> None:
    require_enabled(smoke_config.enable_auth_extended, reason="SMOKE_ENABLE_AUTH_EXTENDED not enabled")

    tenant_entry = smoke_seed["tenants"][smoke_config.tenant_slug]
    tenant_id = tenant_entry["tenant_id"]

    tokens = await login_for_tokens(
        http_client,
        smoke_config,
        tenant_id,
        email=smoke_config.unverified_email,
    )
    headers = bearer_headers(tokens["access_token"])

    send_resp = await http_client.post("/api/v1/auth/email/send", headers=headers)
    assert send_resp.status_code == 202, send_resp.text

    token_resp = await http_client.post(
        "/api/v1/test-fixtures/email-verification-token",
        json={"email": smoke_config.unverified_email},
    )
    assert token_resp.status_code == 201, token_resp.text
    token = token_resp.json().get("token")
    assert token

    verify_resp = await http_client.post(
        "/api/v1/auth/email/verify",
        json={"token": token},
    )
    assert verify_resp.status_code == 200, verify_resp.text


async def test_password_reset_flow(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
) -> None:
    require_enabled(smoke_config.enable_auth_extended, reason="SMOKE_ENABLE_AUTH_EXTENDED not enabled")

    forgot_resp = await http_client.post(
        "/api/v1/auth/password/forgot",
        json={"email": smoke_config.password_reset_email},
    )
    assert forgot_resp.status_code == 202, forgot_resp.text

    token_resp = await http_client.post(
        "/api/v1/test-fixtures/password-reset-token",
        json={"email": smoke_config.password_reset_email},
    )
    assert token_resp.status_code == 201, token_resp.text
    token = token_resp.json().get("token")
    assert token

    confirm_resp = await http_client.post(
        "/api/v1/auth/password/confirm",
        json={"token": token, "new_password": _strong_password("SmokeReset")},
    )
    assert confirm_resp.status_code == 200, confirm_resp.text


async def test_password_change_and_admin_reset(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_state: SmokeState,
    smoke_seed: dict[str, Any],
) -> None:
    require_enabled(smoke_config.enable_auth_extended, reason="SMOKE_ENABLE_AUTH_EXTENDED not enabled")

    tenant_entry = smoke_seed["tenants"][smoke_config.tenant_slug]
    tenant_id = tenant_entry["tenant_id"]

    change_tokens = await login_for_tokens(
        http_client,
        smoke_config,
        tenant_id,
        email=smoke_config.password_change_email,
    )
    change_headers = bearer_headers(change_tokens["access_token"])

    change_resp = await http_client.post(
        "/api/v1/auth/password/change",
        json={
            "current_password": smoke_config.admin_password,
            "new_password": _strong_password("SmokeChange"),
        },
        headers=change_headers,
    )
    assert change_resp.status_code == 200, change_resp.text

    target_user_id = tenant_entry["users"][smoke_config.password_reset_email]["user_id"]
    reset_resp = await http_client.post(
        "/api/v1/auth/password/reset",
        json={
            "user_id": target_user_id,
            "new_password": _strong_password("SmokeAdminReset"),
        },
        headers=auth_headers(smoke_state),
    )
    assert reset_resp.status_code == 200, reset_resp.text
