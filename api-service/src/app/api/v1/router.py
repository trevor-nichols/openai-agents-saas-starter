"""Aggregate router for version 1 of the public API."""

from fastapi import APIRouter

from app.api.v1.agents.router import router as agents_router
from app.api.v1.auth.router import router as auth_router
from app.api.v1.billing.router import router as billing_router
from app.api.v1.chat.router import router as chat_router
from app.api.v1.conversations.router import router as conversations_router
from app.api.v1.logs.router import router as logs_router
from app.api.v1.status.router import legacy_router as status_legacy_router
from app.api.v1.status.router import router as status_router
from app.api.v1.tenants.router import router as tenants_router
from app.api.v1.test_fixtures.router import router as test_fixtures_router
from app.api.v1.tools.router import router as tools_router
from app.core.config import get_settings

router = APIRouter()
router.include_router(auth_router)
router.include_router(chat_router)
router.include_router(agents_router)
router.include_router(conversations_router)
router.include_router(tools_router)
router.include_router(status_router)
router.include_router(status_legacy_router)
router.include_router(tenants_router)

settings = get_settings()
if settings.enable_billing:
    router.include_router(billing_router)
if settings.use_test_fixtures:
    router.include_router(test_fixtures_router)
if settings.enable_frontend_log_ingest:
    router.include_router(logs_router)
