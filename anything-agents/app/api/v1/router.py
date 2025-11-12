"""Aggregate router for version 1 of the public API."""

from fastapi import APIRouter

from app.api.v1.agents.router import router as agents_router
from app.api.v1.auth.router import router as auth_router
from app.api.v1.billing.router import router as billing_router
from app.api.v1.chat.router import router as chat_router
from app.api.v1.conversations.router import router as conversations_router
from app.api.v1.status.router import router as status_router
from app.api.v1.tools.router import router as tools_router
from app.core.config import get_settings

router = APIRouter()
router.include_router(auth_router)
router.include_router(chat_router)
router.include_router(agents_router)
router.include_router(conversations_router)
router.include_router(tools_router)
router.include_router(status_router)

settings = get_settings()
if settings.enable_billing:
    router.include_router(billing_router)
