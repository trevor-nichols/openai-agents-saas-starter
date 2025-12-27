from __future__ import annotations

import uuid

import httpx
import pytest

from tests.smoke.http.config import SmokeConfig
from tests.smoke.http.helpers import require_enabled


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_contact_submission(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
) -> None:
    require_enabled(smoke_config.enable_contact, reason="SMOKE_ENABLE_CONTACT not enabled")

    token = uuid.uuid4().hex
    payload = {
        "name": "Smoke Contact",
        "email": f"smoke-contact+{token}@example.com",
        "company": "Smoke Test Co",
        "topic": "Smoke",
        "message": "Smoke test contact submission message.",
        "honeypot": "",
    }
    headers = {
        "User-Agent": "smoke-suite",
        "X-Forwarded-For": "127.0.0.1",
    }

    resp = await http_client.post("/api/v1/contact", json=payload, headers=headers)
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body.get("success") is True
    data = body.get("data")
    assert isinstance(data, dict)
    assert isinstance(data.get("reference_id"), str)
    assert isinstance(data.get("delivered"), bool)
    assert data.get("suppressed") is False
