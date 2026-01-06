"""Platform operator router."""

from fastapi import APIRouter

from app.api.v1.platform import routes_features, routes_tenants

router = APIRouter(prefix="/platform", tags=["platform"])
router.include_router(routes_tenants.router)
router.include_router(routes_features.router)

__all__ = ["router"]
