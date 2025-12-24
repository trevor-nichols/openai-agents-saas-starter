from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, cast

stripe_module: Any | None
try:  # pragma: no cover - optional dependency
    import stripe as _stripe_module
    stripe_module = _stripe_module
except ImportError:  # pragma: no cover - handled at runtime
    stripe_module = None

from starter_cli.core import CLIError
from starter_cli.services.stripe.provisioner import (
    StripeClient,
    StripePrice,
    StripeProduct,
)


def require_stripe_sdk() -> Any:
    if stripe_module is None:  # pragma: no cover - runtime dependency
        raise CLIError(
            "Missing dependency 'stripe'. Install with `pip install './apps/api-service[dev]'`."
        )
    return stripe_module


@dataclass(slots=True)
class StripeSDKClient(StripeClient):
    _stripe: Any

    def search_product_by_metadata(self, *, key: str, value: str) -> StripeProduct | None:
        search_query = f"metadata['{key}']:'{value}'"
        products = self._stripe.Product.search(query=search_query, limit=1)
        if products.data:
            product: Any = products.data[0]
            return StripeProduct(id=product.id, name=product.name)
        return None

    def update_product_name(self, *, product_id: str, name: str) -> None:
        self._stripe.Product.modify(product_id, name=name)

    def create_product(self, *, name: str, metadata: dict[str, str]) -> StripeProduct:
        product = self._stripe.Product.create(name=name, metadata=metadata)
        return StripeProduct(id=product.id, name=product.name)

    def list_prices(self, *, product_id: str) -> Iterable[StripePrice]:
        prices: Any = self._stripe.Price.list(product=product_id, active=True, limit=100)
        for price in prices.auto_paging_iter():
            recurring = getattr(price, "recurring", None) or {}
            unit_amount = cast(int | None, getattr(price, "unit_amount", None)) or 0
            yield StripePrice(
                id=price.id,
                currency=price.currency,
                unit_amount=unit_amount,
                recurring=cast(dict[str, object], recurring),
            )

    def create_price(
        self,
        *,
        product_id: str,
        currency: str,
        unit_amount: int,
        nickname: str,
        trial_days: int,
        metadata: dict[str, str],
    ) -> StripePrice:
        price = self._stripe.Price.create(
            product=product_id,
            currency=currency,
            unit_amount=unit_amount,
            nickname=nickname,
            recurring={"interval": "month", "trial_period_days": trial_days},
            metadata=metadata,
        )
        recurring = getattr(price, "recurring", None) or {}
        unit_amount_value = cast(int | None, getattr(price, "unit_amount", None)) or 0
        return StripePrice(
            id=price.id,
            currency=price.currency,
            unit_amount=unit_amount_value,
            recurring=cast(dict[str, object], recurring),
        )


def build_stripe_client(*, api_key: str) -> StripeSDKClient:
    stripe = require_stripe_sdk()
    stripe.api_key = api_key
    return StripeSDKClient(_stripe=stripe)


__all__ = ["StripeSDKClient", "build_stripe_client", "require_stripe_sdk"]
