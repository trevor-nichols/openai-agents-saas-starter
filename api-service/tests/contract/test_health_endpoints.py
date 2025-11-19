# File: tests/test_health.py
# Purpose: Tests for health check endpoints
# Dependencies: pytest, fastapi
# Used by: pytest for testing health endpoints

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_check():
    """Test basic health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


def test_readiness_check():
    """Test readiness check endpoint."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "timestamp" in data
    assert "version" in data
