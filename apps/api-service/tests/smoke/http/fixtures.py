from __future__ import annotations

from typing import Any, Dict

import httpx
import pytest

from .config import SmokeConfig


async def apply_test_fixtures(client: httpx.AsyncClient, cfg: SmokeConfig) -> Dict[str, Any]:
    tenant_payload: Dict[str, Any] = {
        "slug": cfg.tenant_slug,
        "name": cfg.tenant_name,
        "users": [
            {
                "email": cfg.admin_email,
                "password": cfg.admin_password,
                "display_name": "Smoke Admin",
                "role": "owner",
                "verify_email": True,
            }
        ],
        "conversations": [
            {
                "key": cfg.fixture_conversation_key,
                "status": "archived",
                "agent_entrypoint": "default",
                "user_email": cfg.admin_email,
                "messages": [
                    {"role": "user", "text": "hello"},
                    {"role": "assistant", "text": "hi there"},
                ],
            }
        ],
        "usage": [],
    }

    if cfg.enable_billing:
        tenant_payload["plan_code"] = "pro"
        tenant_payload["billing_email"] = cfg.admin_email

    payload = {"tenants": [tenant_payload]}

    response = await client.post("/api/v1/test-fixtures/apply", json=payload)

    if response.status_code == 404:
        pytest.skip("Test fixtures endpoint disabled; set USE_TEST_FIXTURES=true for smoke suite.")

    assert response.status_code == 201, f"Failed to apply fixtures: {response.text}"
    return response.json()


__all__ = ["apply_test_fixtures"]
