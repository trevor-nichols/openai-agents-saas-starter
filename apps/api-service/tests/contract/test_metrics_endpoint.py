"""Contract tests for the Prometheus metrics endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from main import app


def test_metrics_endpoint_exposes_auth_series() -> None:
    client = TestClient(app)

    # Prime counters so scrape output contains observable samples.
    client.get("/.well-known/jwks.json")

    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    body = response.text
    assert "jwks_requests_total" in body
    assert "jwt_verifications_total" in body
    assert "service_account_issuance_total" in body

    client.close()
