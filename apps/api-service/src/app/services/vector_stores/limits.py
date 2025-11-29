"""Plan-aware resolver for vector store guardrail limits.

This module centralizes how vector limits are derived so that the service can
stay agnostic to whether billing/entitlements are enabled. When billing is off
or plan entitlements omit a limit, we fall back to the static settings values
defined in AIProviderSettingsMixin.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from app.core.settings import Settings
from app.domain.billing import PlanFeature
from app.services.billing.billing_service import BillingService


@dataclass(frozen=True)
class VectorLimits:
    max_file_bytes: int
    max_total_bytes: int | None
    max_files_per_store: int
    max_stores_per_tenant: int


VECTOR_FEATURE_KEYS = {
    "vector.max_file_bytes": "bytes",
    "vector.total_bytes_per_tenant": "bytes",
    "vector.files_per_store": "count",
    "vector.stores_per_tenant": "count",
}


def _feature_lookup(features: Iterable[PlanFeature]) -> dict[str, PlanFeature]:
    return {feature.key: feature for feature in features}


class VectorLimitResolver:
    """Derive effective limits using plan entitlements when available."""

    def __init__(self, *, billing_service: BillingService | None, settings_factory):
        self._billing = billing_service
        self._settings_factory = settings_factory

    async def resolve(self, tenant_id: str) -> VectorLimits:
        settings: Settings = self._settings_factory()

        # Defaults from settings
        defaults = VectorLimits(
            max_file_bytes=settings.vector_max_file_mb * 1024 * 1024,
            max_total_bytes=settings.vector_max_total_bytes,
            max_files_per_store=settings.vector_max_files_per_store,
            max_stores_per_tenant=settings.vector_max_stores_per_tenant,
        )

        # Bail early when billing/guardrails are off
        if not settings.enable_billing or self._billing is None:
            return defaults

        subscription = await self._billing.get_subscription(tenant_id)
        if subscription is None:
            return defaults

        plan = await self._billing.get_plan(subscription.plan_code)
        feature_map = _feature_lookup(plan.features)

        def _value(key: str, fallback):
            feature = feature_map.get(key)
            limit = feature.hard_limit if feature else None
            return fallback if limit is None else limit

        return VectorLimits(
            max_file_bytes=_value("vector.max_file_bytes", defaults.max_file_bytes),
            max_total_bytes=_value("vector.total_bytes_per_tenant", defaults.max_total_bytes),
            max_files_per_store=_value("vector.files_per_store", defaults.max_files_per_store),
            max_stores_per_tenant=_value(
                "vector.stores_per_tenant", defaults.max_stores_per_tenant
            ),
        )


__all__ = ["VectorLimitResolver", "VectorLimits", "VECTOR_FEATURE_KEYS"]
