"""Feature gating dependencies."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.api.dependencies.tenant import (
    TenantContext,
    TenantRole,
    get_tenant_context,
    require_tenant_role,
)
from app.domain.feature_flags import FeatureKey
from app.services.feature_flags import FeatureFlagService, get_feature_flag_service


def require_feature(feature: FeatureKey):
    """Ensure a feature is enabled for the current tenant."""

    async def _dependency(
        context: TenantContext = Depends(get_tenant_context),
        service: FeatureFlagService = Depends(get_feature_flag_service),
    ) -> TenantContext:
        if not await service.is_enabled(context.tenant_id, feature):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{feature.value} feature is disabled for this tenant.",
            )
        return context

    return _dependency


def require_feature_for_role(feature: FeatureKey, *roles: TenantRole):
    """Ensure a tenant role and enabled feature in one dependency."""

    async def _dependency(
        context: TenantContext = Depends(require_tenant_role(*roles)),
        service: FeatureFlagService = Depends(get_feature_flag_service),
    ) -> TenantContext:
        if not await service.is_enabled(context.tenant_id, feature):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{feature.value} feature is disabled for this tenant.",
            )
        return context

    return _dependency


__all__ = ["require_feature", "require_feature_for_role"]
