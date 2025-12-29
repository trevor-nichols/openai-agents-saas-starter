"""Aggregate tenant settings routes."""

from fastapi import APIRouter

from app.api.v1.tenants import routes_invites, routes_members, routes_settings

router = APIRouter(prefix="/tenants", tags=["tenants"])
router.include_router(routes_members.router)
router.include_router(routes_invites.router)
router.include_router(routes_settings.router)

__all__ = ["router"]
