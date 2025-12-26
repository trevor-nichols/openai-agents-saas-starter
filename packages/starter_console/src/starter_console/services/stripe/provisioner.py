from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from .catalog import PLAN_CATALOG, PLAN_METADATA_KEY, PlanConfig


@dataclass(frozen=True, slots=True)
class StripeProduct:
    id: str
    name: str


@dataclass(frozen=True, slots=True)
class StripePrice:
    id: str
    currency: str
    unit_amount: int
    recurring: dict[str, object]


class StripeClient(Protocol):
    def search_product_by_metadata(self, *, key: str, value: str) -> StripeProduct | None: ...

    def update_product_name(self, *, product_id: str, name: str) -> None: ...

    def create_product(self, *, name: str, metadata: dict[str, str]) -> StripeProduct: ...

    def list_prices(self, *, product_id: str) -> Iterable[StripePrice]: ...

    def create_price(
        self,
        *,
        product_id: str,
        currency: str,
        unit_amount: int,
        nickname: str,
        trial_days: int,
        metadata: dict[str, str],
    ) -> StripePrice: ...


@dataclass(frozen=True, slots=True)
class ProvisionedPlan:
    code: str
    name: str
    amount_cents: int
    price_id: str


@dataclass(frozen=True, slots=True)
class ProvisionResult:
    price_map: dict[str, str]
    plans: tuple[ProvisionedPlan, ...]


@dataclass(slots=True)
class StripeProvisioner:
    client: StripeClient
    currency: str
    trial_days: int
    catalog: tuple[PlanConfig, ...] = PLAN_CATALOG

    def provision(self, plan_amounts: dict[str, int]) -> ProvisionResult:
        price_map: dict[str, str] = {}
        plans: list[ProvisionedPlan] = []
        for plan in self.catalog:
            amount = plan_amounts[plan.code]
            product = self._ensure_product(plan)
            price = self._ensure_price(product.id, plan, amount)
            price_map[plan.code] = price.id
            plans.append(
                ProvisionedPlan(
                    code=plan.code,
                    name=plan.name,
                    amount_cents=amount,
                    price_id=price.id,
                )
            )
        return ProvisionResult(price_map=price_map, plans=tuple(plans))

    def _ensure_product(self, plan: PlanConfig) -> StripeProduct:
        product = self.client.search_product_by_metadata(key=PLAN_METADATA_KEY, value=plan.code)
        if product:
            if product.name != plan.name:
                self.client.update_product_name(product_id=product.id, name=plan.name)
            return product
        return self.client.create_product(name=plan.name, metadata={PLAN_METADATA_KEY: plan.code})

    def _ensure_price(self, product_id: str, plan: PlanConfig, amount_cents: int) -> StripePrice:
        for price in self.client.list_prices(product_id=product_id):
            recurring = price.recurring or {}
            if (
                price.currency == self.currency
                and price.unit_amount == amount_cents
                and recurring.get("interval") == "month"
                and recurring.get("trial_period_days") == self.trial_days
            ):
                return price
        return self.client.create_price(
            product_id=product_id,
            currency=self.currency,
            unit_amount=amount_cents,
            nickname=f"{plan.code.title()} Monthly",
            trial_days=self.trial_days,
            metadata={PLAN_METADATA_KEY: plan.code},
        )


__all__ = [
    "ProvisionResult",
    "ProvisionedPlan",
    "StripeClient",
    "StripePrice",
    "StripeProduct",
    "StripeProvisioner",
]
