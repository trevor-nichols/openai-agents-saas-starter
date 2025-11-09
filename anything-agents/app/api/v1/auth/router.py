"""Authentication endpoints for API v1."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.auth.routes_email import router as email_routes
from app.api.v1.auth.routes_passwords import router as password_routes
from app.api.v1.auth.routes_service_accounts import router as service_account_routes
from app.api.v1.auth.routes_sessions import router as session_routes
from app.api.v1.auth.routes_signup import router as signup_routes

router = APIRouter(prefix="/auth", tags=["auth"])
router.include_router(session_routes)
router.include_router(email_routes)
router.include_router(password_routes)
router.include_router(service_account_routes)
router.include_router(signup_routes)
