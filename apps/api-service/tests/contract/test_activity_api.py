from __future__ import annotations

import importlib
import json
import os
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ENABLE_ACTIVITY_STREAM", "true")

pytestmark = pytest.mark.auto_migrations(enabled=True)

from app.api.dependencies.auth import require_current_user  # noqa: E402
from app.domain.activity import ActivityEvent, ActivityEventStatePage, ActivityEventWithState  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture(scope="function")
def tenant_id() -> str:
    return str(uuid4())


@pytest.fixture(autouse=True)
def override_current_user(tenant_id: str):
    def _stub_user():
        return {
            "user_id": "test-user",
            "subject": "user:test-user",
            "payload": {
                "scope": "activity:read",
                "tenant_id": tenant_id,
                "roles": ["admin"],
            },
        }

    previous = app.dependency_overrides.get(require_current_user)
    app.dependency_overrides[require_current_user] = _stub_user
    try:
        yield
    finally:
        if previous is None:
            app.dependency_overrides.pop(require_current_user, None)
        else:
            app.dependency_overrides[require_current_user] = previous


@pytest.fixture(scope="function")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_list_activity_filters_and_pagination(
    client: TestClient, tenant_id: str, monkeypatch
) -> None:
    now = datetime.now(tz=UTC)
    events = [
        ActivityEvent(
            id="evt-1",
            tenant_id=tenant_id,
            action="workflow.run.started",
            created_at=now - timedelta(seconds=2),
            actor_id=str(uuid4()),
            actor_type="user",
            metadata={"workflow_key": "analysis_code", "run_id": "run-1"},
        ),
        ActivityEvent(
            id="evt-2",
            tenant_id=tenant_id,
            action="auth.login.success",
            created_at=now - timedelta(seconds=1),
            actor_id=str(uuid4()),
            actor_type="user",
            metadata={"user_id": "user-1"},
        ),
    ]

    async def _mock_list(tenant: str, user_id: str, *, limit: int, cursor: str | None = None, filters=None):
        assert tenant == tenant_id
        filtered_events = list(events)
        if filters and getattr(filters, "action", None):
            filtered_events = [ev for ev in events if ev.action == filters.action]

        next_cursor = "cursor-1"
        state_items = [
            ActivityEventWithState(
                **event.__dict__,
                read_state="unread",
            )
            for event in filtered_events[:limit]
        ]
        return ActivityEventStatePage(
            items=state_items,
            next_cursor=next_cursor,
            unread_count=len(state_items),
        )

    activity_router_module = importlib.import_module("app.api.v1.activity.router")

    monkeypatch.setattr(
        activity_router_module.activity_service,
        "list_events_with_state",
        AsyncMock(side_effect=_mock_list),
    )

    first = client.get("/api/v1/activity", params={"limit": 2})
    assert first.status_code == 200
    payload = first.json()
    assert len(payload["items"]) == 2
    assert payload["next_cursor"] == "cursor-1"
    assert payload["unread_count"] == 2
    assert all(item["tenant_id"] == tenant_id for item in payload["items"])

    filtered = client.get(
        "/api/v1/activity",
        params={"action": "workflow.run.started", "limit": 10},
    )
    assert filtered.status_code == 200
    filtered_items = filtered.json()["items"]
    assert filtered_items
    assert all(item["action"] == "workflow.run.started" for item in filtered_items)
    assert all(item["tenant_id"] == tenant_id for item in filtered_items)


@pytest.mark.asyncio
async def test_activity_stream_returns_events(tenant_id: str, monkeypatch) -> None:
    stream_payload = {
        "id": "evt-1",
        "tenant_id": tenant_id,
        "action": "workflow.run.started",
        "metadata": {"workflow_key": "analysis_code", "run_id": "run-123"},
    }

    class _FakeStream:
        def __init__(self):
            self._messages = [json.dumps(stream_payload)]

        async def next_message(self, timeout: float | None = None) -> str | None:
            return self._messages.pop(0) if self._messages else None

        async def close(self) -> None:
            return None

    fake_stream = _FakeStream()

    async def _subscribe(tenant: str):
        assert tenant == tenant_id
        return fake_stream

    import importlib

    activity_router_module = importlib.import_module("app.api.v1.activity.router")

    monkeypatch.setattr(
        activity_router_module.activity_service,
        "subscribe",
        AsyncMock(side_effect=_subscribe),
    )

    current_user = {
        "user_id": "test-user",
        "payload": {
            "tenant_id": tenant_id,
            "scope": "activity:read",
            "roles": ["admin"],
        },
    }

    response = await activity_router_module.stream_activity_events(
        current_user=current_user, tenant_id_header=None, tenant_role_header=None
    )

    chunks: list[bytes] = []
    async for chunk in response.body_iterator:
        if chunk:
            chunks.append(chunk)
            break

    assert chunks
    text = chunks[0].decode("utf-8")
    assert text.startswith("data: ")
    payload = json.loads(text[6:])
    assert payload["action"] == "workflow.run.started"
    assert payload["tenant_id"] == tenant_id
