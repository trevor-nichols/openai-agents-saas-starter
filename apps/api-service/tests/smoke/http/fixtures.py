from __future__ import annotations

from typing import Any, Dict

import httpx
import pytest

from .config import SmokeConfig


async def apply_test_fixtures(client: httpx.AsyncClient, cfg: SmokeConfig) -> Dict[str, Any]:
    usage_period_start = "2025-01-01"
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
        "usage_counters": [
            {
                "period_start": usage_period_start,
                "granularity": "day",
                "requests": 1,
                "input_tokens": 10,
                "output_tokens": 5,
                "storage_bytes": 0,
            }
        ],
    }

    if cfg.enable_billing:
        tenant_payload["plan_code"] = "pro"
        tenant_payload["billing_email"] = cfg.admin_email
        tenant_payload["usage"] = [
            {
                "feature_key": "smoke.requests",
                "quantity": 1,
                "unit": "requests",
                "period_start": f"{usage_period_start}T00:00:00+00:00",
            }
        ]

    if cfg.enable_assets:
        tenant_payload["assets"] = [
            {
                "key": "seeded-asset-image",
                "asset_type": "image",
                "source_tool": "image_generation",
                "filename": "smoke-image.png",
                "mime_type": "image/png",
                "size_bytes": 12,
                "agent_key": "triage",
                "conversation_key": cfg.fixture_conversation_key,
                "user_email": cfg.admin_email,
                "metadata": {"fixture": "smoke"},
            }
        ]

    payload = {"tenants": [tenant_payload]}

    response = await client.post("/api/v1/test-fixtures/apply", json=payload)

    if response.status_code == 404:
        pytest.skip("Test fixtures endpoint disabled; set USE_TEST_FIXTURES=true for smoke suite.")

    assert response.status_code == 201, f"Failed to apply fixtures: {response.text}"
    return response.json()


__all__ = ["apply_test_fixtures"]
