"""Unit tests for Stripe mapping helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from app.infrastructure.stripe.mappers import (
    extract_default_payment_method_id,
    to_invoice_line,
    to_subscription,
)


class Dummy:
    def __init__(self, **kwargs: object) -> None:
        self.__dict__.update(kwargs)


def test_extract_default_payment_method_id_from_dict() -> None:
    customer = Dummy(invoice_settings={"default_payment_method": {"id": "pm_123"}})
    assert extract_default_payment_method_id(customer) == "pm_123"


def test_extract_default_payment_method_id_from_object() -> None:
    customer = Dummy(invoice_settings=Dummy(default_payment_method="pm_456"))
    assert extract_default_payment_method_id(customer) == "pm_456"


def test_to_subscription_maps_items_and_schedule() -> None:
    item = Dummy(id="si_1", price=Dummy(id="price_1"), quantity=2)
    subscription = Dummy(
        id="sub_1",
        customer="cus_1",
        status="active",
        cancel_at_period_end=False,
        current_period_start=1_700_000_000,
        current_period_end=1_700_000_100,
        trial_end=None,
        items=Dummy(data=[item]),
        schedule={"id": "sched_1"},
        metadata={"foo": "bar"},
    )

    result = to_subscription(subscription)

    assert result.primary_item is not None
    assert result.primary_item.id == "si_1"
    assert result.primary_item.price_id == "price_1"
    assert result.schedule_id == "sched_1"
    assert result.metadata == {"foo": "bar"}
    assert result.current_period_start == datetime.fromtimestamp(1_700_000_000, tz=UTC)


def test_to_invoice_line_maps_price_fields() -> None:
    line = Dummy(
        description="Test charge",
        amount=2500,
        currency="usd",
        quantity=2,
        price=Dummy(id="price_1", unit_amount=1250),
    )

    result = to_invoice_line(line)

    assert result.price_id == "price_1"
    assert result.unit_amount == 1250
    assert result.amount == 2500
