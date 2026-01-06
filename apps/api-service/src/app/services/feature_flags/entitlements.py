"""Service for managing tenant feature entitlements (platform-only)."""

from __future__ import annotations

from app.domain.feature_flags import (
    TENANT_ENTITLEMENT_KEYS,
    FeatureEntitlementsSnapshot,
    FeatureKey,
    extract_tenant_entitlements,
    tenant_feature_key,
)
from app.domain.tenant_settings import TenantSettingsRepository, TenantSettingsSnapshot


class FeatureEntitlementService:
    """Manage tenant-level feature entitlements."""

    def __init__(self, repository: TenantSettingsRepository | None = None) -> None:
        self._repository = repository

    def set_repository(self, repository: TenantSettingsRepository) -> None:
        self._repository = repository

    @property
    def repository(self) -> TenantSettingsRepository:
        return self._require_repository()

    async def get_entitlements(self, tenant_id: str) -> FeatureEntitlementsSnapshot:
        snapshot = await self._fetch_snapshot(tenant_id)
        entitlements = extract_tenant_entitlements(snapshot.flags)
        return FeatureEntitlementsSnapshot(tenant_id=tenant_id, entitlements=entitlements)

    async def update_entitlements(
        self,
        tenant_id: str,
        *,
        updates: dict[FeatureKey, bool | None],
    ) -> FeatureEntitlementsSnapshot:
        merged_updates: dict[str, bool | None] = {}
        for key, value in updates.items():
            if key not in TENANT_ENTITLEMENT_KEYS:
                continue
            flag_key = tenant_feature_key(key)
            if value is None:
                merged_updates[flag_key] = None
            else:
                merged_updates[flag_key] = bool(value)

        updated = await self._require_repository().patch_flags(
            tenant_id,
            updates=merged_updates,
        )
        entitlements = extract_tenant_entitlements(updated.flags)
        return FeatureEntitlementsSnapshot(tenant_id=tenant_id, entitlements=entitlements)

    async def _fetch_snapshot(self, tenant_id: str) -> TenantSettingsSnapshot:
        snapshot = await self._require_repository().fetch(tenant_id)
        if snapshot:
            return snapshot
        return TenantSettingsSnapshot(
            tenant_id=tenant_id,
            billing_contacts=[],
            billing_webhook_url=None,
            plan_metadata={},
            flags={},
        )

    def _require_repository(self) -> TenantSettingsRepository:
        if self._repository is None:
            raise RuntimeError(
                "FeatureEntitlementService repository has not been configured."
            )
        return self._repository


def get_feature_entitlement_service() -> FeatureEntitlementService:
    from app.bootstrap.container import get_container

    return get_container().feature_entitlement_service


__all__ = ["FeatureEntitlementService", "get_feature_entitlement_service"]
