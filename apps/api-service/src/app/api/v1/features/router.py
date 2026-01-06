"""Feature snapshot endpoints for authenticated tenants."""

from fastapi import APIRouter, Depends

from app.api.dependencies.tenant import TenantContext, TenantRole, require_tenant_role
from app.api.models.features import FeatureSnapshotResponse
from app.services.feature_flags import FeatureFlagService, get_feature_flag_service

router = APIRouter(prefix="/features", tags=["features"])


@router.get("", response_model=FeatureSnapshotResponse)
async def get_feature_snapshot(
    context: TenantContext = Depends(
        require_tenant_role(
            TenantRole.VIEWER,
            TenantRole.MEMBER,
            TenantRole.ADMIN,
            TenantRole.OWNER,
        )
    ),
    service: FeatureFlagService = Depends(get_feature_flag_service),
) -> FeatureSnapshotResponse:
    snapshot = await service.snapshot_for_tenant(context.tenant_id)
    return FeatureSnapshotResponse.from_snapshot(snapshot)


__all__ = ["router"]
