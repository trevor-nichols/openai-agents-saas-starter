"""Contract tests for the public platform status endpoints."""

import os
from xml.etree import ElementTree as ET

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("RATE_LIMIT_REDIS_URL", os.environ["REDIS_URL"])
os.environ.setdefault("AUTH_CACHE_REDIS_URL", os.environ["REDIS_URL"])
os.environ.setdefault("SECURITY_TOKEN_REDIS_URL", os.environ["REDIS_URL"])
os.environ.setdefault("AUTO_RUN_MIGRATIONS", "false")
os.environ.setdefault("ENABLE_BILLING", "false")

from main import app  # pylint: disable=wrong-import-position

client = TestClient(app)


def test_get_platform_status_snapshot() -> None:
    response = client.get("/api/v1/status")
    assert response.status_code == 200

    payload = response.json()
    assert payload["overview"]["state"]
    assert len(payload["services"]) >= 1
    assert len(payload["incidents"]) >= 1
    assert "generated_at" in payload


def test_get_platform_status_rss() -> None:
    response = client.get("/api/v1/status.rss")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/rss+xml")

    document = ET.fromstring(response.content)
    channel = document.find("channel")
    assert channel is not None
    items = channel.findall("item")
    assert items, "Expected at least one incident item in the RSS feed"
