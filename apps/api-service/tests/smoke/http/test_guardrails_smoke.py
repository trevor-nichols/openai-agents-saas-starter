from __future__ import annotations

import httpx
import pytest

from tests.smoke.http.auth import auth_headers
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_guardrails_catalog(http_client: httpx.AsyncClient, smoke_state: SmokeState) -> None:
    headers = auth_headers(smoke_state)

    guardrails = await http_client.get("/api/v1/guardrails", headers=headers)
    assert guardrails.status_code == 200
    guardrail_items = guardrails.json()
    assert isinstance(guardrail_items, list)

    presets = await http_client.get("/api/v1/guardrails/presets", headers=headers)
    assert presets.status_code == 200
    preset_items = presets.json()
    assert isinstance(preset_items, list)

    if guardrail_items:
        key = guardrail_items[0].get("key")
        assert key
        detail = await http_client.get(f"/api/v1/guardrails/{key}", headers=headers)
        assert detail.status_code == 200

    if preset_items:
        key = preset_items[0].get("key")
        assert key
        detail = await http_client.get(f"/api/v1/guardrails/presets/{key}", headers=headers)
        assert detail.status_code == 200
