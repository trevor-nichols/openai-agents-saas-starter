"""Contract tests for notification preference endpoints with overrides."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies.auth import require_current_user
from app.api.dependencies.tenant import TenantContext, TenantRole
from app.services.notification_preferences import get_notification_preference_service
import app.api.v1.users.routes_notifications as notifications_module
from main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    prev_user = app.dependency_overrides.get(require_current_user)
    prev_service = app.dependency_overrides.get(get_notification_preference_service)
    dep = notifications_module.router.routes[0].dependant.dependencies[1].call  # type: ignore[attr-defined]
    prev_tenant = app.dependency_overrides.get(dep)

    def _user():
        return {"user_id": str(uuid4())}

    svc = AsyncMock()
    pref_obj = AsyncMock()
    pref_obj.id = uuid4()
    pref_obj.channel = "email"
    pref_obj.category = "alerts"
    pref_obj.enabled = False
    pref_obj.tenant_id = None
    svc.upsert_preference.return_value = pref_obj
    svc.list_preferences.return_value = [pref_obj]

    app.dependency_overrides[require_current_user] = _user
    app.dependency_overrides[dep] = lambda: TenantContext(
        tenant_id=str(uuid4()), role=TenantRole.VIEWER, user={"user_id": str(uuid4())}
    )
    app.dependency_overrides[notifications_module._service] = lambda: svc
    notifications_module.get_notification_preference_service = lambda: svc
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        if prev_user is not None:
            app.dependency_overrides[require_current_user] = prev_user
        else:
            app.dependency_overrides.pop(require_current_user, None)
        if prev_tenant is not None:
            app.dependency_overrides[dep] = prev_tenant
        else:
            app.dependency_overrides.pop(dep, None)
        if prev_service is not None:
            app.dependency_overrides[get_notification_preference_service] = prev_service
        else:
            app.dependency_overrides.pop(get_notification_preference_service, None)


def test_upsert_pref(client: TestClient) -> None:
    resp = client.put(
        "/api/v1/users/notification-preferences",
        headers={"X-Tenant-Id": str(uuid4())},
        json={"channel": "email", "category": "alerts", "enabled": False},
    )
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False


def test_list_prefs(client: TestClient) -> None:
    resp = client.get(
        "/api/v1/users/notification-preferences",
        headers={"X-Tenant-Id": str(uuid4())},
    )
    assert resp.status_code == 200
    assert resp.json()[0]["channel"] == "email"
