"""Repository query helpers for billing services."""

from __future__ import annotations

from app.domain.billing import BillingPlan, BillingRepository, TenantSubscription
from app.services.billing.errors import (
    PlanNotFoundError,
    SubscriptionNotFoundError,
    SubscriptionStateError,
    raise_invalid_tenant,
)


async def get_subscription(
    repository: BillingRepository, tenant_id: str
) -> TenantSubscription | None:
    try:
        return await repository.get_subscription(tenant_id)
    except ValueError as exc:
        raise_invalid_tenant(exc)


async def require_subscription(
    repository: BillingRepository, tenant_id: str
) -> TenantSubscription:
    subscription = await get_subscription(repository, tenant_id)
    if subscription is None:
        raise SubscriptionNotFoundError(
            f"Tenant '{tenant_id}' does not have an active subscription."
        )
    return subscription


async def list_plans(repository: BillingRepository) -> list[BillingPlan]:
    return await repository.list_plans()


async def ensure_plan_exists(
    repository: BillingRepository, plan_code: str
) -> BillingPlan:
    plans = await list_plans(repository)
    for plan in plans:
        if plan.code == plan_code:
            return plan
    raise PlanNotFoundError(f"Plan '{plan_code}' not found.")


def require_processor_subscription_id(subscription: TenantSubscription) -> str:
    if not subscription.processor_subscription_id:
        raise SubscriptionStateError("Subscription is missing processor identifier.")
    return subscription.processor_subscription_id


__all__ = [
    "ensure_plan_exists",
    "get_subscription",
    "list_plans",
    "require_processor_subscription_id",
    "require_subscription",
]
