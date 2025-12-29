"""Plan-to-Stripe price resolution."""

from __future__ import annotations

from collections.abc import Callable

from app.core.settings import Settings
from app.services.billing.payment_gateway import PaymentGatewayError


def resolve_price_id(
    plan_code: str, *, settings_factory: Callable[[], Settings]
) -> str:
    settings = settings_factory()
    mapping = settings.stripe_product_price_map or {}
    price_id = mapping.get(plan_code)
    if not price_id:
        raise PaymentGatewayError(
            f"No Stripe price configured for plan '{plan_code}'.",
            code="price_mapping_missing",
        )
    return price_id


__all__ = ["resolve_price_id"]
