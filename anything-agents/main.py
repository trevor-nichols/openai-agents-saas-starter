# File: main.py
# Purpose: FastAPI application entry point for anything-agents
# Dependencies: app/core/config.py, app/api, app/presentation
# Used by: uvicorn server to run the application

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from redis.asyncio import Redis

from app.api.errors import register_exception_handlers
from app.api.router import api_router
from app.core.config import Settings, enforce_secret_overrides, get_settings
from app.infrastructure.db import (
    dispose_engine,
    get_async_sessionmaker,
    get_engine,
    init_engine,
)
from app.infrastructure.openai.sessions import configure_sdk_session_store
from app.infrastructure.persistence.billing import PostgresBillingRepository
from app.infrastructure.persistence.conversations.postgres import PostgresConversationRepository
from app.infrastructure.persistence.stripe.repository import (
    StripeEventRepository,
    configure_stripe_event_repository,
)
from app.infrastructure.security.vault_kv import configure_vault_secret_manager
from app.middleware.logging import LoggingMiddleware
from app.presentation import health as health_routes
from app.presentation import metrics as metrics_routes
from app.presentation import well_known as well_known_routes
from app.presentation.webhooks import stripe as stripe_webhook
from app.services.billing_events import RedisBillingEventBackend, billing_events_service
from app.services.billing_service import billing_service
from app.services.conversation_service import conversation_service
from app.services.payment_gateway import stripe_gateway
from app.services.rate_limit_service import rate_limiter
from app.services.stripe_dispatcher import stripe_event_dispatcher
from app.services.stripe_retry_worker import stripe_dispatch_retry_worker

# =============================================================================
# MODULE CONSTANTS
# =============================================================================

logger = logging.getLogger(__name__)
_STRIPE_TROUBLESHOOTING_DOC = "docs/billing/stripe-setup.md#startup-validation--troubleshooting"

# =============================================================================
# LIFESPAN EVENTS
# =============================================================================


def _ensure_billing_prerequisites(settings: Settings) -> None:
    missing = settings.required_stripe_envs_missing()

    if missing:
        missing_envs = ", ".join(missing)
        raise RuntimeError(
            "ENABLE_BILLING=true requires Stripe configuration. "
            f"Set {missing_envs} (see {_STRIPE_TROUBLESHOOTING_DOC})."
        )

    _log_billing_configuration(settings)


def _log_billing_configuration(settings: Settings) -> None:
    """Emit a masked summary of billing configuration state for observability."""
    summary = settings.stripe_configuration_summary()
    plan_count = summary.get("plan_count", 0)
    logger.info(
        "Stripe billing configuration validated; %s plan(s) mapped.",
        plan_count,
        extra={"stripe_config": summary},
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events."""
    settings = get_settings()
    warnings = settings.secret_warnings()
    try:
        enforce_secret_overrides(settings)
    except RuntimeError:
        raise
    else:
        if warnings and not settings.should_enforce_secret_overrides():
            logger.warning(
                "Default development secrets detected (environment=%s): %s",
                settings.environment,
                "; ".join(warnings),
            )
    configure_vault_secret_manager(settings)

    session_factory = None
    stripe_repo: StripeEventRepository | None = None
    redis_backend_configured = False
    retry_worker_started = False
    rate_limit_configured = False
    rate_limit_client: Redis | None = None

    if settings.redis_url:
        rate_limit_client = Redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=False,
        )
        rate_limiter.configure(
            redis=rate_limit_client,
            prefix=settings.rate_limit_key_prefix,
        )
        rate_limit_configured = True

    if settings.enable_billing:
        _ensure_billing_prerequisites(settings)
        billing_service.set_gateway(stripe_gateway)

    await init_engine(run_migrations=settings.auto_run_migrations)
    engine = get_engine()
    if engine is None:
        raise RuntimeError("Database engine failed to initialise; cannot configure sessions.")
    configure_sdk_session_store(engine)
    session_factory = get_async_sessionmaker()
    postgres_repository = PostgresConversationRepository(session_factory)
    conversation_service.set_repository(postgres_repository)

    if settings.enable_billing:
        billing_service.set_repository(PostgresBillingRepository(session_factory))
        stripe_repo = StripeEventRepository(session_factory)
        configure_stripe_event_repository(stripe_repo)
        stripe_event_dispatcher.configure(repository=stripe_repo, billing=billing_service)
        if settings.enable_billing_retry_worker:
            stripe_dispatch_retry_worker.configure(
                repository=stripe_repo, dispatcher=stripe_event_dispatcher
            )
            await stripe_dispatch_retry_worker.start()
            retry_worker_started = True
        else:
            logger.info("Stripe dispatch retry worker disabled by configuration")

        if settings.enable_billing_stream:
            redis_url = settings.billing_events_redis_url or settings.redis_url
            if not redis_url:
                raise RuntimeError(
                    "ENABLE_BILLING_STREAM requires BILLING_EVENTS_REDIS_URL or REDIS_URL"
                )
            redis_client = Redis.from_url(redis_url, encoding="utf-8", decode_responses=False)
            backend = RedisBillingEventBackend(redis_client)
            billing_events_service.configure(backend=backend, repository=stripe_repo)
            if settings.enable_billing_stream_replay:
                await billing_events_service.startup()
                redis_backend_configured = True
            else:
                logger.info("Billing stream replay/startup disabled by configuration")
    try:
        yield
    finally:
        if redis_backend_configured:
            await billing_events_service.shutdown()
        if retry_worker_started:
            await stripe_dispatch_retry_worker.shutdown()
        if rate_limit_configured:
            await rate_limiter.shutdown()
        await dispose_engine()


# =============================================================================
# APPLICATION FACTORY
# =============================================================================


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    settings = get_settings()

    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        debug=settings.debug,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # =============================================================================
    # MIDDLEWARE CONFIGURATION
    # =============================================================================

    # Trusted hosts middleware (allow env-configured hosts, widen during debug)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"] if settings.debug else settings.get_allowed_hosts_list(),
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_allowed_origins_list(),
        allow_credentials=True,
        allow_methods=settings.get_allowed_methods_list(),
        allow_headers=settings.get_allowed_headers_list(),
    )

    # Custom logging middleware
    app.add_middleware(LoggingMiddleware)

    # =============================================================================
    # ROUTER REGISTRATION
    # =============================================================================

    register_exception_handlers(app)

    # Health check endpoints (non-versioned)
    app.include_router(health_routes.router, tags=["health"])
    app.include_router(well_known_routes.router)
    app.include_router(metrics_routes.router)
    if settings.enable_billing:
        app.include_router(stripe_webhook.router)

    # Versioned API surface
    app.include_router(api_router, prefix="/api", tags=["api"])

    return app


# =============================================================================
# APPLICATION INSTANCE
# =============================================================================

app = create_application()

# =============================================================================
# ROOT ENDPOINT
# =============================================================================


@app.get("/")
async def root():
    """
    Root endpoint providing basic service information.

    Returns:
        dict: Service information
    """
    settings = get_settings()
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "description": settings.app_description,
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1",
        "chat": "/api/v1/chat",
        "agents": "/api/v1/agents",
    }
