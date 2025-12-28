"""Pure policy helpers for billing plan and subscription decisions."""

from __future__ import annotations

from app.domain.billing import BillingPlan
from app.services.billing.models import PlanChangeTiming


def merge_subscription_metadata(
    existing: dict[str, str] | None,
    incoming: dict[str, str] | None,
) -> dict[str, str]:
    merged: dict[str, str] = dict(existing or {})
    reserved_keys = {
        "pending_plan_code",
        "pending_plan_effective_at",
        "pending_seat_count",
        "processor_schedule_id",
    }
    if incoming:
        for key, value in incoming.items():
            if value is None:
                continue
            key_str = str(key)
            if key_str in reserved_keys:
                continue
            merged[key_str] = str(value)

    for reserved in reserved_keys:
        merged.pop(reserved, None)

    return merged


def resolve_plan_change_timing(
    timing: PlanChangeTiming,
    *,
    current_plan: BillingPlan,
    target_plan: BillingPlan,
    current_seat_count: int,
    target_seat_count: int,
) -> PlanChangeTiming:
    if timing != PlanChangeTiming.AUTO:
        return timing
    if (
        current_plan.interval == target_plan.interval
        and current_plan.interval_count == target_plan.interval_count
    ):
        current_total = current_plan.price_cents * max(current_seat_count, 1)
        target_total = target_plan.price_cents * max(target_seat_count, 1)
        if target_total > current_total:
            return PlanChangeTiming.IMMEDIATE
        return PlanChangeTiming.PERIOD_END
    return PlanChangeTiming.PERIOD_END


__all__ = ["merge_subscription_metadata", "resolve_plan_change_timing"]
