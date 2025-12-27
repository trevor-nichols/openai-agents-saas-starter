from __future__ import annotations

import httpx

from tests.smoke.http.config import SmokeConfig


async def login_for_tokens(
    client: httpx.AsyncClient,
    cfg: SmokeConfig,
    tenant_id: str,
    *,
    email: str | None = None,
    password: str | None = None,
) -> dict[str, str]:
    payload = {
        "email": email or cfg.admin_email,
        "password": password or cfg.admin_password,
        "tenant_id": tenant_id,
    }
    headers = {
        "User-Agent": "smoke-suite",
        "X-Forwarded-For": "127.0.0.1",
    }
    response = await client.post("/api/v1/auth/token", json=payload, headers=headers)
    if response.status_code != 200:
        raise AssertionError(f"Login failed: {response.status_code} {response.text}")
    return response.json()


def auth_headers(state, *, tenant_role: str = "owner") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {state.access_token}",
        "X-Tenant-Id": state.tenant_id,
        "X-Tenant-Role": tenant_role,
    }


def bearer_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


__all__ = ["login_for_tokens", "auth_headers", "bearer_headers"]
