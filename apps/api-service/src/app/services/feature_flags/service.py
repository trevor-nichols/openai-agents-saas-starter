"""Service for evaluating effective feature flags for a tenant."""

from __future__ import annotations

from collections.abc import Callable

from app.core.settings import Settings, get_settings
from app.domain.feature_flags import (
    FeatureKey,
    FeatureSnapshot,
    extract_tenant_entitlements,
    tenant_feature_key,
)
from app.domain.tenant_settings import TenantSettingsRepository, TenantSettingsSnapshot


class FeatureFlagService:
    """Resolve effective feature access for a tenant."""

    def __init__(
        self,
        *,
        repository: TenantSettingsRepository | None = None,
        settings_factory: Callable[[], Settings] = get_settings,
    ) -> None:
        self._repository = repository
        self._settings_factory = settings_factory

    def set_repository(self, repository: TenantSettingsRepository) -> None:
        self._repository = repository

    @property
    def repository(self) -> TenantSettingsRepository:
        return self._require_repository()

    async def snapshot_for_tenant(self, tenant_id: str) -> FeatureSnapshot:
        settings = self._settings_factory()
        tenant_snapshot = await self._fetch_tenant_snapshot(tenant_id)
        entitlements = extract_tenant_entitlements(tenant_snapshot.flags)

        billing_enabled = self._apply_tenant_override(
            settings.enable_billing,
            entitlements.get(FeatureKey.BILLING),
        )
        billing_stream_enabled = bool(
            billing_enabled and settings.enable_billing_stream
        )

        return FeatureSnapshot(
            billing_enabled=billing_enabled,
            billing_stream_enabled=billing_stream_enabled,
        )

    async def is_enabled(self, tenant_id: str, feature: FeatureKey) -> bool:
        snapshot = await self.snapshot_for_tenant(tenant_id)
        return snapshot.is_enabled(feature)

    async def tenant_entitlement_override(
        self, tenant_id: str, feature: FeatureKey
    ) -> bool | None:
        tenant_snapshot = await self._fetch_tenant_snapshot(tenant_id)
        key = tenant_feature_key(feature)
        if key in tenant_snapshot.flags:
            return bool(tenant_snapshot.flags[key])
        return None

    async def _fetch_tenant_snapshot(self, tenant_id: str) -> TenantSettingsSnapshot:
        repository = self._require_repository()
        snapshot = await repository.fetch(tenant_id)
        if snapshot:
            return snapshot
        return TenantSettingsSnapshot(tenant_id=tenant_id)

    def _require_repository(self) -> TenantSettingsRepository:
        if self._repository is None:
            raise RuntimeError("FeatureFlagService repository has not been configured.")
        return self._repository

    @staticmethod
    def _apply_tenant_override(global_enabled: bool, override: bool | None) -> bool:
        if not global_enabled:
            return False
        if override is None:
            return True
        return bool(override)


def get_feature_flag_service() -> FeatureFlagService:
    from app.bootstrap.container import get_container

    return get_container().feature_flag_service


__all__ = ["FeatureFlagService", "get_feature_flag_service"]
