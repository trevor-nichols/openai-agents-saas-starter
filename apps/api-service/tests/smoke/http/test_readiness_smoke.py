from __future__ import annotations

import httpx
import pytest


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_jwks_exposes_keys(http_client: httpx.AsyncClient) -> None:
    response = await http_client.get("/.well-known/jwks.json")
    assert response.status_code == 200
    body = response.json()
    keys = body.get("keys") or []
    assert isinstance(keys, list)
    assert keys, "JWKS response contained no keys"
    assert all(key.get("kid") for key in keys)


async def test_metrics_includes_auth_series(http_client: httpx.AsyncClient) -> None:
    # Prime counters so the scrape contains samples.
    prime = await http_client.get("/.well-known/jwks.json")
    assert prime.status_code == 200

    response = await http_client.get("/metrics")
    assert response.status_code == 200
    text = response.text
    for metric in (
        "jwks_requests_total",
        "jwt_verifications_total",
        "service_account_issuance_total",
    ):
        assert metric in text
