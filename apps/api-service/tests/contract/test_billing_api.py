"""Contract tests for billing endpoints (enable_billing on)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Generator
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.utils.contract_auth import make_user_payload
from tests.utils.contract_env import TEST_TENANT_ID

from app.api.dependencies.auth import require_current_user  # noqa: E402
from app.api.v1.billing import router as billing_router  # noqa: E402
from app.domain.billing import BillingPlan, TenantSubscription  # noqa: E402


def _stub_owner_user() -> dict[str, Any]:
    return make_user_payload(roles=("owner",))


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    app = FastAPI()
    app.include_router(
        billing_router.router,
        prefix="/api/v1",
    )
    app.dependency_overrides[require_current_user] = _stub_owner_user
    with TestClient(app) as test_client:
        yield test_client


def test_list_billing_plans_returns_catalog(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = BillingPlan(
        code="starter",
        name="Starter",
        interval="month",
        interval_count=1,
        price_cents=1200,
        currency="usd",
        seat_included=1,
        is_active=True,
    )
    monkeypatch.setattr(
        billing_router.billing_service,
        "list_plans",
        AsyncMock(return_value=[plan]),
    )

    response = client.get("/api/v1/billing/plans")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload[0]["code"] == "starter"


def test_get_tenant_subscription_tenant_mismatch(client: TestClient) -> None:
    response = client.get("/api/v1/billing/tenants/other-tenant/subscription")
    assert response.status_code == 403


def test_get_tenant_subscription_returns_payload(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = datetime.now(UTC)
    subscription = TenantSubscription(
        tenant_id=TEST_TENANT_ID,
        plan_code="starter",
        status="active",
        auto_renew=True,
        billing_email="billing@example.com",
        starts_at=now,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        seat_count=1,
        processor="stripe",
        processor_subscription_id="sub_test",
        processor_customer_id="cus_test",
    )
    monkeypatch.setattr(
        billing_router.billing_service,
        "get_subscription",
        AsyncMock(return_value=subscription),
    )

    response = client.get(f"/api/v1/billing/tenants/{TEST_TENANT_ID}/subscription")
    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == TEST_TENANT_ID
    assert payload["plan_code"] == "starter"
    assert payload["status"] == "active"
