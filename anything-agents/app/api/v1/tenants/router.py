"""Aggregate tenant settings routes."""

from fastapi import APIRouter

from app.api.v1.tenants import routes_settings

router = APIRouter(prefix="/tenants", tags=["tenants"])
router.include_router(routes_settings.router)

__all__ = ["router"]
