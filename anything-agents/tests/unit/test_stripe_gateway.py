"""Unit tests for the StripeGateway adapter."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from app.core.config import Settings
from app.infrastructure.stripe import (
    StripeClientError,
    StripeCustomer,
    StripeSubscription,
    StripeSubscriptionItem,
    StripeUsageRecord,
)
from app.services.billing.payment_gateway import PaymentGatewayError, StripeGateway


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
        self.created_customers: list[dict[str, Any]] = []
        self.created_subscriptions: list[dict[str, Any]] = []
        self.updated_subscription_calls: list[dict[str, Any]] = []
        self.updated_emails: list[str] = []
        self.cancelled: list[bool] = []
        self.usage_calls: list[dict[str, Any]] = []

    async def create_customer(self, *, email: str | None, tenant_id: str) -> StripeCustomer:
        payload = {"email": email, "tenant_id": tenant_id}
        self.created_customers.append(payload)
        return self._customer(email)

    async def create_subscription(
        self,
        *,
        customer_id: str,
        price_id: str,
        quantity: int,
        auto_renew: bool,
        trial_period_days: int | None = None,
        metadata: dict[str, str] | None = None,
    ) -> StripeSubscription:
        payload: dict[str, Any] = {
            "customer_id": customer_id,
            "price_id": price_id,
            "quantity": quantity,
            "auto_renew": auto_renew,
            "metadata": metadata or {},
        }
        if trial_period_days is not None:
            payload["trial_period_days"] = trial_period_days
        self.created_subscriptions.append(payload)
        return self.subscription

    async def retrieve_subscription(self, subscription_id: str) -> StripeSubscription:
        assert subscription_id == self.subscription.id
        return self.subscription

    async def modify_subscription(
        self,
        subscription: StripeSubscription,
        *,
        auto_renew: bool | None = None,
        seat_count: int | None = None,
    ) -> StripeSubscription:
        self.updated_subscription_calls.append(
            {"auto_renew": auto_renew, "seat_count": seat_count}
        )
        return subscription

    async def cancel_subscription(
        self, subscription_id: str, *, cancel_at_period_end: bool
    ) -> StripeSubscription:
        self.cancelled.append(cancel_at_period_end)
        return self.subscription

    async def update_customer_email(self, customer_id: str, email: str) -> StripeCustomer:
        self.updated_emails.append(email)
        return self._customer(email)

    async def create_usage_record(
        self,
        subscription_item_id: str,
        *,
        quantity: int,
        timestamp: int,
        idempotency_key: str,
        feature_key: str,
    ) -> StripeUsageRecord:
        payload = {
            "subscription_item_id": subscription_item_id,
            "quantity": quantity,
            "timestamp": timestamp,
            "idempotency_key": idempotency_key,
            "feature_key": feature_key,
        }
        self.usage_calls.append(payload)
        return StripeUsageRecord(
            id="usg_123",
            subscription_item_id=subscription_item_id,
            quantity=quantity,
            timestamp=datetime.now(UTC),
        )

    def _customer(self, email: str | None) -> StripeCustomer:
        return StripeCustomer(id="cus_123", email=email)


def _settings(price_map: dict[str, str] | None = None) -> Settings:
    return Settings.model_validate(
        {
            "STRIPE_SECRET_KEY": "sk_test_key",
            "STRIPE_PRODUCT_PRICE_MAP": price_map or {},
        }
    )


@pytest.mark.asyncio
async def test_start_subscription_returns_metadata():
    client = FakeStripeClient()
    settings = _settings({"starter": "price_123"})
    gateway = StripeGateway(client=client, settings_factory=lambda: settings)

    result = await gateway.start_subscription(
        tenant_id="tenant",
        plan_code="starter",
        billing_email="owner@example.com",
        auto_renew=True,
        seat_count=2,
        trial_days=None,
    )

    assert result.metadata is not None
    assert result.metadata["stripe_price_id"] == "price_123"
    assert result.metadata["stripe_subscription_item_id"] == "si_123"
    assert client.created_customers
    assert client.created_subscriptions[0]["quantity"] == 2


@pytest.mark.asyncio
async def test_start_subscription_threads_trial_days():
    client = FakeStripeClient()
    settings = _settings({"starter": "price_123"})
    gateway = StripeGateway(client=client, settings_factory=lambda: settings)

    await gateway.start_subscription(
        tenant_id="tenant",
        plan_code="starter",
        billing_email=None,
        auto_renew=True,
        seat_count=1,
        trial_days=7,
    )

    assert client.created_subscriptions[0].get("trial_period_days") == 7


@pytest.mark.asyncio
async def test_update_subscription_updates_quantity_and_email():
    client = FakeStripeClient()
    settings = _settings({"starter": "price_123"})
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
    settings = _settings({"starter": "price_123"})
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
    settings = _settings({})
    gateway = StripeGateway(client=client, settings_factory=lambda: settings)

    with pytest.raises(PaymentGatewayError) as exc_info:
        await gateway.start_subscription(
            tenant_id="tenant",
            plan_code="unknown",
            billing_email=None,
            auto_renew=True,
            seat_count=1,
            trial_days=None,
        )

    assert exc_info.value.code == "price_mapping_missing"


@pytest.mark.asyncio
async def test_gateway_emits_metrics_on_success(monkeypatch: pytest.MonkeyPatch):
    calls: list[dict[str, object]] = []

    def fake_observe(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(
        "app.services.billing.payment_gateway.observe_stripe_gateway_operation", fake_observe
    )

    client = FakeStripeClient()
    settings = _settings({"starter": "price_123"})
    gateway = StripeGateway(client=client, settings_factory=lambda: settings)

    await gateway.start_subscription(
        tenant_id="tenant",
        plan_code="starter",
        billing_email=None,
        auto_renew=True,
        seat_count=1,
        trial_days=None,
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
        "app.services.billing.payment_gateway.observe_stripe_gateway_operation", fake_observe
    )

    class ExplodingClient(FakeStripeClient):
        async def create_customer(
            self, *, email: str | None, tenant_id: str
        ) -> StripeCustomer:
            raise StripeClientError("customer.create", "boom", code="api_error")

    settings = _settings({"starter": "price_123"})
    gateway = StripeGateway(client=ExplodingClient(), settings_factory=lambda: settings)

    with pytest.raises(PaymentGatewayError) as exc_info:
        await gateway.start_subscription(
            tenant_id="tenant",
            plan_code="starter",
            billing_email=None,
            auto_renew=True,
            seat_count=1,
            trial_days=None,
        )

    assert exc_info.value.code == "api_error"
    assert calls, "expected metrics to capture Stripe error"
    assert calls[-1]["result"] == "api_error"
