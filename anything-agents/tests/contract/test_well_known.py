"""Contract tests for JWKS publication."""

from __future__ import annotations

from fastapi.testclient import TestClient

from main import app


def test_jwks_endpoint_returns_active_and_next_keys() -> None:
    client = TestClient(app)

    response = client.get("/.well-known/jwks.json")

    assert response.status_code == 200
    payload = response.json()
    kids = {entry["kid"] for entry in payload["keys"]}
    assert kids == {"ed25519-active-test", "ed25519-next-test"}
    assert "Cache-Control" in response.headers
    assert "ETag" in response.headers
    assert "Last-Modified" in response.headers

    etag = response.headers["ETag"]
    conditional = client.get("/.well-known/jwks.json", headers={"If-None-Match": etag})
    assert conditional.status_code == 304
    assert conditional.text == ""
    assert conditional.headers["ETag"] == etag

    client.close()
