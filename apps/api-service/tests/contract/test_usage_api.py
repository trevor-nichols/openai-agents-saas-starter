"""Contract tests for usage counters endpoint with overrides."""

from __future__ import annotations

from collections.abc import Generator
from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies.tenant import TenantContext, TenantRole, require_tenant_role
from app.api.v1.usage.router import router as usage_router
import app.api.v1.usage.router as usage_module
from app.services.usage_counters import get_usage_counter_service
from main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    dep = usage_router.routes[0].dependant.dependencies[0].call  # type: ignore[attr-defined]
    prev_dep = app.dependency_overrides.get(dep)
    prev_svc = app.dependency_overrides.get(get_usage_counter_service)

    tenant_id = uuid4()

    def _tenant():
        return TenantContext(tenant_id=str(tenant_id), role=TenantRole.VIEWER, user={"user_id": "u"})

    svc = AsyncMock()
    svc.list_for_tenant.return_value = [
        SimpleNamespace(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=None,
            period_start=date.today(),
            granularity=SimpleNamespace(value="day"),
            input_tokens=1,
            output_tokens=2,
            requests=3,
            storage_bytes=0,
            updated_at=datetime.now(),
        )
    ]

    app.dependency_overrides[dep] = _tenant
    usage_module.get_usage_counter_service = lambda: svc
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        if prev_dep is not None:
            app.dependency_overrides[dep] = prev_dep
        else:
            app.dependency_overrides.pop(dep, None)
        if prev_svc is not None:
            app.dependency_overrides[get_usage_counter_service] = prev_svc
        else:
            app.dependency_overrides.pop(get_usage_counter_service, None)


def test_usage_list(client: TestClient) -> None:
    resp = client.get("/api/v1/usage")
    assert resp.status_code == 200
    body = resp.json()
    assert body[0]["requests"] == 3
