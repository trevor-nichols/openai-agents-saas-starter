from __future__ import annotations

import base64
import hmac
import struct
import time
from typing import Any

import httpx
import pytest

from tests.smoke.http.auth import bearer_headers, login_for_tokens
from tests.smoke.http.config import SmokeConfig
from tests.smoke.http.helpers import require_enabled


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


def _totp(secret: str, *, step: int = 30, digits: int = 6, offset: int = 0) -> int:
    key = base64.b32decode(secret + "=" * (-len(secret) % 8))
    counter = int(time.time() // step) + offset
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, "sha1").digest()
    pos = digest[-1] & 0x0F
    code = struct.unpack(">I", digest[pos : pos + 4])[0] & 0x7FFFFFFF
    return code % (10**digits)


def _current_totp(secret: str) -> str:
    return f"{_totp(secret):06d}"


async def test_mfa_totp_flow(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_seed: dict[str, Any],
) -> None:
    require_enabled(smoke_config.enable_auth_mfa, reason="SMOKE_ENABLE_AUTH_MFA not enabled")

    tenant_entry = smoke_seed["tenants"][smoke_config.tenant_slug]
    tenant_id = tenant_entry["tenant_id"]

    tokens = await login_for_tokens(
        http_client,
        smoke_config,
        tenant_id,
        email=smoke_config.mfa_email,
    )
    headers = bearer_headers(tokens["access_token"])

    list_resp = await http_client.get("/api/v1/auth/mfa", headers=headers)
    assert list_resp.status_code == 200, list_resp.text

    enroll_resp = await http_client.post("/api/v1/auth/mfa/totp/enroll", headers=headers)
    assert enroll_resp.status_code == 201, enroll_resp.text
    enroll_body = enroll_resp.json()
    secret = enroll_body.get("secret")
    method_id = enroll_body.get("method_id")
    assert secret and method_id

    verify_resp = await http_client.post(
        "/api/v1/auth/mfa/totp/verify",
        json={"method_id": method_id, "code": _current_totp(secret)},
        headers=headers,
    )
    assert verify_resp.status_code == 200, verify_resp.text

    recovery_resp = await http_client.post(
        "/api/v1/auth/mfa/recovery/regenerate",
        headers=headers,
    )
    assert recovery_resp.status_code == 200, recovery_resp.text
    codes = recovery_resp.json().get("codes")
    assert isinstance(codes, list) and codes

    challenge_resp = await http_client.post(
        "/api/v1/auth/token",
        json={
            "email": smoke_config.mfa_email,
            "password": smoke_config.admin_password,
            "tenant_id": tenant_id,
        },
    )
    assert challenge_resp.status_code == 202, challenge_resp.text
    challenge_body = challenge_resp.json()
    challenge_token = challenge_body.get("challenge_token")
    assert challenge_token

    complete_resp = await http_client.post(
        "/api/v1/auth/mfa/complete",
        json={
            "challenge_token": challenge_token,
            "method_id": method_id,
            "code": _current_totp(secret),
        },
    )
    assert complete_resp.status_code == 200, complete_resp.text
    complete_body = complete_resp.json()
    assert complete_body.get("access_token")

    revoke_resp = await http_client.delete(
        f"/api/v1/auth/mfa/{method_id}",
        headers=headers,
    )
    assert revoke_resp.status_code == 200, revoke_resp.text
