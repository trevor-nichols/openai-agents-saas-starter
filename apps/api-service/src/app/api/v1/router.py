"""Aggregate router for version 1 of the public API."""

from fastapi import APIRouter

from app.api.v1.activity.router import router as activity_router
from app.api.v1.agents.router import router as agents_router
from app.api.v1.assets.router import router as assets_router
from app.api.v1.auth.router import router as auth_router
from app.api.v1.billing.router import router as billing_router
from app.api.v1.chat.router import router as chat_router
from app.api.v1.contact.router import router as contact_router
from app.api.v1.containers.router import router as containers_router
from app.api.v1.conversations.ledger_router import router as conversation_ledger_router
from app.api.v1.conversations.router import router as conversations_router
from app.api.v1.guardrails.router import router as guardrails_router
from app.api.v1.logs.router import router as logs_router
from app.api.v1.openai_files.router import router as openai_files_router
from app.api.v1.status.router import router as status_router
from app.api.v1.storage.router import router as storage_router
from app.api.v1.tenants.router import router as tenants_router
from app.api.v1.test_fixtures.router import router as test_fixtures_router
from app.api.v1.tools.router import router as tools_router
from app.api.v1.usage.router import router as usage_router
from app.api.v1.users.routes_consents import router as user_consents_router
from app.api.v1.users.routes_notifications import router as user_notifications_router
from app.api.v1.users.routes_profile import router as user_profile_router
from app.api.v1.vector_stores.router import router as vector_stores_router
from app.api.v1.workflows.replay_router import router as workflows_replay_router
from app.api.v1.workflows.router import router as workflows_router
from app.core.settings import get_settings

router = APIRouter()
router.include_router(auth_router)
router.include_router(chat_router)
router.include_router(agents_router)
router.include_router(assets_router)
router.include_router(guardrails_router)
router.include_router(workflows_router)
router.include_router(workflows_replay_router)
router.include_router(conversations_router)
router.include_router(conversation_ledger_router)
router.include_router(tools_router)
router.include_router(activity_router)
router.include_router(containers_router)
router.include_router(vector_stores_router)
router.include_router(storage_router)
router.include_router(openai_files_router)
router.include_router(contact_router)
router.include_router(status_router)
router.include_router(tenants_router)
router.include_router(user_consents_router)
router.include_router(user_notifications_router)
router.include_router(user_profile_router)
router.include_router(usage_router)

settings = get_settings()
if settings.enable_billing:
    router.include_router(billing_router)
if settings.use_test_fixtures:
    router.include_router(test_fixtures_router)
if settings.enable_frontend_log_ingest:
    router.include_router(logs_router)
