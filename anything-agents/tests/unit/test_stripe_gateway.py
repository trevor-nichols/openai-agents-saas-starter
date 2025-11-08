"""Unit tests for the StripeGateway adapter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from app.infrastructure.stripe import (
    StripeClientError,
    StripeCustomer,
    StripeSubscription,
    StripeSubscriptionItem,
    StripeUsageRecord,
)
from app.services.payment_gateway import (
    PaymentGatewayError,
    StripeGateway,
)


@dataclass
class FakeSettings:
    stripe_secret_key: str = "sk_test_key"
    stripe_product_price_map: dict[str, str] | None = None


class FakeStripeClient:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.subscription = StripeSubscription(
            id="sub_123",
            customer_id="cus_123",
            status="active",
            cancel_at_period_end=False,
            current_period_start=now,
            current_period_end=now,
            trial_end=None,
            items=[StripeSubscriptionItem(id="si_123", price_id="price_123", quantity=1)],
        )
        self.created_customers: list[dict[str, object]] = []
        self.created_subscriptions: list[dict[str, object]] = []
        self.updated_subscription_calls: list[dict[str, object]] = []
        self.updated_emails: list[str] = []
        self.cancelled: list[bool] = []
        self.usage_calls: list[dict[str, object]] = []

    async def create_customer(self, *, email: str | None, tenant_id: str):
        self.created_customers.append({"email": email, "tenant_id": tenant_id})
        return self._customer(email)

    async def create_subscription(self, **payload):
        self.created_subscriptions.append(payload)
        return self.subscription

    async def retrieve_subscription(self, subscription_id: str):
        assert subscription_id == self.subscription.id
        return self.subscription

    async def modify_subscription(
        self,
        subscription: StripeSubscription,
        *,
        auto_renew: bool | None = None,
        seat_count: int | None = None,
    ):
        self.updated_subscription_calls.append({"auto_renew": auto_renew, "seat_count": seat_count})
        return subscription

    async def cancel_subscription(self, subscription_id: str, *, cancel_at_period_end: bool):
        self.cancelled.append(cancel_at_period_end)
        return self.subscription

    async def update_customer_email(self, customer_id: str, email: str):
        self.updated_emails.append(email)
        return self._customer(email)

    async def create_usage_record(self, *_, **payload):
        self.usage_calls.append(payload)
        return StripeUsageRecord(
            id="usg_123",
            subscription_item_id="si_123",
            quantity=payload["quantity"],
            timestamp=datetime.now(UTC),
        )

    def _customer(self, email: str | None):
        return StripeCustomer(id="cus_123", email=email)


@pytest.mark.asyncio
async def test_start_subscription_returns_metadata():
    client = FakeStripeClient()
    settings = FakeSettings(stripe_product_price_map={"starter": "price_123"})
    gateway = StripeGateway(client=client, settings_factory=lambda: settings)

    result = await gateway.start_subscription(
        tenant_id="tenant",
        plan_code="starter",
        billing_email="owner@example.com",
        auto_renew=True,
        seat_count=2,
    )

    assert result.metadata["stripe_price_id"] == "price_123"
    assert result.metadata["stripe_subscription_item_id"] == "si_123"
    assert client.created_customers
    assert client.created_subscriptions[0]["quantity"] == 2


@pytest.mark.asyncio
async def test_update_subscription_updates_quantity_and_email():
    client = FakeStripeClient()
    settings = FakeSettings(stripe_product_price_map={"starter": "price_123"})
    gateway = StripeGateway(client=client, settings_factory=lambda: settings)

    await gateway.update_subscription(
        "sub_123",
        auto_renew=False,
        seat_count=5,
        billing_email="billing@example.com",
    )

    assert client.updated_subscription_calls
    change = client.updated_subscription_calls[0]
    assert change["auto_renew"] is False
    assert change["seat_count"] == 5
    assert client.updated_emails[-1] == "billing@example.com"


@pytest.mark.asyncio
async def test_record_usage_passes_idempotency_key():
    client = FakeStripeClient()
    settings = FakeSettings(stripe_product_price_map={"starter": "price_123"})
    gateway = StripeGateway(client=client, settings_factory=lambda: settings)

    await gateway.record_usage(
        "sub_123",
        feature_key="messages",
        quantity=10,
        idempotency_key="usage-123",
    )

    assert client.usage_calls[0]["idempotency_key"] == "usage-123"


@pytest.mark.asyncio
async def test_missing_price_mapping_raises_error():
    client = FakeStripeClient()
    settings = FakeSettings(stripe_product_price_map={})
    gateway = StripeGateway(client=client, settings_factory=lambda: settings)

    with pytest.raises(PaymentGatewayError) as exc_info:
        await gateway.start_subscription(
            tenant_id="tenant",
            plan_code="unknown",
            billing_email=None,
            auto_renew=True,
            seat_count=1,
        )

    assert exc_info.value.code == "price_mapping_missing"


@pytest.mark.asyncio
async def test_gateway_emits_metrics_on_success(monkeypatch: pytest.MonkeyPatch):
    calls: list[dict[str, object]] = []

    def fake_observe(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(
        "app.services.payment_gateway.observe_stripe_gateway_operation", fake_observe
    )

    client = FakeStripeClient()
    settings = FakeSettings(stripe_product_price_map={"starter": "price_123"})
    gateway = StripeGateway(client=client, settings_factory=lambda: settings)

    await gateway.start_subscription(
        tenant_id="tenant",
        plan_code="starter",
        billing_email=None,
        auto_renew=True,
        seat_count=1,
    )

    assert calls, "expected gateway metrics to be recorded"
    success_call = calls[-1]
    assert success_call["operation"] == "start_subscription"
    assert success_call["plan_code"] == "starter"
    assert success_call["result"] == "success"


@pytest.mark.asyncio
async def test_stripe_errors_wrapped_with_gateway_error(monkeypatch: pytest.MonkeyPatch):
    calls: list[dict[str, object]] = []

    def fake_observe(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(
        "app.services.payment_gateway.observe_stripe_gateway_operation", fake_observe
    )

    class ExplodingClient(FakeStripeClient):
        async def create_customer(self, *, email: str | None, tenant_id: str):  # type: ignore[override]
            raise StripeClientError("customer.create", "boom", code="api_error")

    settings = FakeSettings(stripe_product_price_map={"starter": "price_123"})
    gateway = StripeGateway(client=ExplodingClient(), settings_factory=lambda: settings)

    with pytest.raises(PaymentGatewayError) as exc_info:
        await gateway.start_subscription(
            tenant_id="tenant",
            plan_code="starter",
            billing_email=None,
            auto_renew=True,
            seat_count=1,
        )

    assert exc_info.value.code == "api_error"
    assert calls, "expected metrics to capture Stripe error"
    assert calls[-1]["result"] == "api_error"
