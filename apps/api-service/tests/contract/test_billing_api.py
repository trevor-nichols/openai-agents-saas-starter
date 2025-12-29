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
from app.domain.billing import (  # noqa: E402
    BillingPlan,
    SubscriptionInvoiceRecord,
    TenantSubscription,
    UsageTotal,
)
from app.services.billing.models import (  # noqa: E402
    PlanChangeResult,
    PlanChangeTiming,
    UpcomingInvoiceLineSnapshot,
    UpcomingInvoicePreview,
)
from app.services.billing.payment_gateway import (  # noqa: E402
    PaymentMethodSummary,
    PortalSessionResult,
    SetupIntentResult,
)


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


def test_list_invoices_returns_payload(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = datetime.now(UTC)
    invoice = SubscriptionInvoiceRecord(
        tenant_id=TEST_TENANT_ID,
        period_start=now,
        period_end=now + timedelta(days=30),
        amount_cents=1200,
        currency="USD",
        status="paid",
        processor_invoice_id="in_123",
        hosted_invoice_url="https://example.com/invoices/in_123",
        created_at=now,
    )
    list_mock = AsyncMock(return_value=[invoice])
    monkeypatch.setattr(billing_router.billing_service, "list_invoices", list_mock)

    response = client.get(
        f"/api/v1/billing/tenants/{TEST_TENANT_ID}/invoices",
        params={"limit": 20, "offset": 0},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["invoice_id"] == "in_123"
    assert payload["items"][0]["amount_cents"] == 1200
    assert payload["next_offset"] is None

    list_mock.assert_awaited_once_with(TEST_TENANT_ID, limit=20, offset=0)


def test_get_invoice_returns_payload(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = datetime.now(UTC)
    invoice = SubscriptionInvoiceRecord(
        tenant_id=TEST_TENANT_ID,
        period_start=now,
        period_end=now + timedelta(days=30),
        amount_cents=2400,
        currency="USD",
        status="paid",
        processor_invoice_id="in_456",
        hosted_invoice_url="https://example.com/invoices/in_456",
        created_at=now,
    )
    get_mock = AsyncMock(return_value=invoice)
    monkeypatch.setattr(billing_router.billing_service, "get_invoice", get_mock)

    response = client.get(
        f"/api/v1/billing/tenants/{TEST_TENANT_ID}/invoices/in_456"
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["invoice_id"] == "in_456"
    assert payload["amount_cents"] == 2400

    get_mock.assert_awaited_once_with(TEST_TENANT_ID, invoice_id="in_456")


def test_create_portal_session_returns_url(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        billing_router.billing_service,
        "create_portal_session",
        AsyncMock(return_value=PortalSessionResult(url="https://portal.example.com")),
    )

    response = client.post(
        f"/api/v1/billing/tenants/{TEST_TENANT_ID}/portal",
        json={"billing_email": "billing@example.com"},
    )
    assert response.status_code == 200
    assert response.json()["url"] == "https://portal.example.com"


def test_start_subscription_omits_email_but_response_preserves(
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
    start_mock = AsyncMock(return_value=subscription)
    monkeypatch.setattr(billing_router.billing_service, "start_subscription", start_mock)

    response = client.post(
        f"/api/v1/billing/tenants/{TEST_TENANT_ID}/subscription",
        json={"plan_code": "starter", "auto_renew": True},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["billing_email"] == "billing@example.com"
    start_mock.assert_awaited_once()


def test_list_payment_methods_returns_items(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        billing_router.billing_service,
        "list_payment_methods",
        AsyncMock(
            return_value=[
                PaymentMethodSummary(
                    id="pm_123",
                    brand="visa",
                    last4="4242",
                    exp_month=12,
                    exp_year=2030,
                    is_default=True,
                )
            ]
        ),
    )

    response = client.get(
        f"/api/v1/billing/tenants/{TEST_TENANT_ID}/payment-methods"
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["id"] == "pm_123"
    assert payload[0]["is_default"] is True


def test_create_setup_intent_returns_payload(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        billing_router.billing_service,
        "create_setup_intent",
        AsyncMock(
            return_value=SetupIntentResult(id="seti_123", client_secret="secret")
        ),
    )

    response = client.post(
        f"/api/v1/billing/tenants/{TEST_TENANT_ID}/payment-methods/setup-intent",
        json={"billing_email": "billing@example.com"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "seti_123"
    assert payload["client_secret"] == "secret"


def test_set_default_payment_method_returns_success(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        billing_router.billing_service,
        "set_default_payment_method",
        AsyncMock(return_value=None),
    )

    response = client.post(
        f"/api/v1/billing/tenants/{TEST_TENANT_ID}/payment-methods/pm_123/default"
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_detach_payment_method_returns_success(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        billing_router.billing_service,
        "detach_payment_method",
        AsyncMock(return_value=None),
    )

    response = client.delete(
        f"/api/v1/billing/tenants/{TEST_TENANT_ID}/payment-methods/pm_123"
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_preview_upcoming_invoice_returns_payload(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = datetime.now(UTC)
    preview = UpcomingInvoicePreview(
        plan_code="starter",
        plan_name="Starter",
        seat_count=2,
        invoice_id="in_123",
        amount_due_cents=1200,
        currency="usd",
        period_start=now,
        period_end=now + timedelta(days=30),
        lines=[
            UpcomingInvoiceLineSnapshot(
                description="Seat charge",
                amount_cents=1200,
                currency="usd",
                quantity=2,
                unit_amount_cents=600,
                price_id="price_123",
            )
        ],
    )
    monkeypatch.setattr(
        billing_router.billing_service,
        "preview_upcoming_invoice",
        AsyncMock(return_value=preview),
    )

    response = client.post(
        f"/api/v1/billing/tenants/{TEST_TENANT_ID}/upcoming-invoice",
        json={"seat_count": 2},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["plan_code"] == "starter"
    assert payload["plan_name"] == "Starter"
    assert payload["amount_due_cents"] == 1200


def test_change_subscription_plan_returns_response(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = datetime.now(UTC)
    subscription = TenantSubscription(
        tenant_id=TEST_TENANT_ID,
        plan_code="pro",
        status="active",
        auto_renew=True,
        billing_email="billing@example.com",
        starts_at=now,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        seat_count=2,
        processor="stripe",
        processor_subscription_id="sub_test",
        processor_customer_id="cus_test",
    )
    result = PlanChangeResult(
        subscription=subscription,
        target_plan_code="pro",
        effective_at=now,
        seat_count=2,
        timing=PlanChangeTiming.IMMEDIATE,
    )
    monkeypatch.setattr(
        billing_router.billing_service,
        "change_subscription_plan",
        AsyncMock(return_value=result),
    )

    response = client.post(
        f"/api/v1/billing/tenants/{TEST_TENANT_ID}/subscription/plan",
        json={"plan_code": "pro", "seat_count": 2, "timing": "immediate"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["target_plan_code"] == "pro"
    assert payload["subscription"]["plan_code"] == "pro"


def test_list_usage_totals_returns_payload(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    period_start = datetime(2025, 1, 1, tzinfo=UTC)
    period_end = datetime(2025, 2, 1, tzinfo=UTC)
    totals = [
        UsageTotal(
            feature_key="tokens",
            unit="tokens",
            quantity=1200,
            window_start=period_start,
            window_end=period_end,
        ),
        UsageTotal(
            feature_key="requests",
            unit="requests",
            quantity=42,
            window_start=period_start,
            window_end=period_end,
        ),
    ]
    get_totals = AsyncMock(return_value=totals)
    monkeypatch.setattr(billing_router.billing_service, "get_usage_totals", get_totals)

    response = client.get(
        f"/api/v1/billing/tenants/{TEST_TENANT_ID}/usage-totals",
        params=[
            ("feature_keys", "tokens"),
            ("feature_keys", "requests"),
            ("period_start", period_start.isoformat()),
            ("period_end", period_end.isoformat()),
        ],
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert payload[0]["feature_key"] == "tokens"
    assert payload[0]["quantity"] == 1200
    window_start = payload[0]["window_start"].replace("Z", "+00:00")
    assert datetime.fromisoformat(window_start) == period_start
    assert payload[1]["feature_key"] == "requests"

    get_totals.assert_awaited_once_with(
        TEST_TENANT_ID,
        feature_keys=["tokens", "requests"],
        period_start=period_start,
        period_end=period_end,
    )
