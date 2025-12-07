"""FastAPI application entry point for api-service."""

import logging
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.errors import register_exception_handlers
from app.api.router import api_router
from app.bootstrap import (
    get_container,
    shutdown_container,
    wire_conversation_query_service,
    wire_title_service,
)
from app.core.provider_validation import (
    ProviderViolation,
    ensure_provider_parity,
    validate_providers,
)
from app.core.settings import (
    Settings,
    enforce_secret_overrides,
    enforce_vault_verification,
    get_settings,
)
from app.infrastructure.activity.redis_backend import RedisActivityEventBackend
from app.infrastructure.billing.events.redis_backend import RedisBillingEventBackend
from app.infrastructure.db import (
    dispose_engine,
    get_async_sessionmaker,
    get_engine,
    init_engine,
)
from app.infrastructure.persistence.activity import (
    SqlAlchemyActivityEventRepository,
    SqlAlchemyActivityInboxRepository,
)
from app.infrastructure.persistence.auth.repository import get_refresh_token_repository
from app.infrastructure.persistence.auth.session_repository import (
    get_user_session_repository,
)
from app.infrastructure.persistence.auth.signup_repository import (
    PostgresSignupInviteRepository,
    PostgresSignupRequestRepository,
)
from app.infrastructure.persistence.auth.user_repository import get_user_repository
from app.infrastructure.persistence.billing import PostgresBillingRepository
from app.infrastructure.persistence.conversations.postgres import (
    PostgresConversationRepository,
)
from app.infrastructure.persistence.status import get_status_subscription_repository
from app.infrastructure.persistence.stripe.repository import (
    StripeEventRepository,
    configure_stripe_event_repository,
)
from app.infrastructure.persistence.tenants import PostgresTenantSettingsRepository
from app.infrastructure.providers.openai import build_openai_provider
from app.infrastructure.redis.factory import get_redis_factory
from app.infrastructure.redis_types import RedisBytesClient
from app.infrastructure.security.vault_kv import configure_vault_secret_manager
from app.middleware.logging import LoggingMiddleware
from app.observability.logging import configure_logging
from app.presentation import health as health_routes
from app.presentation import metrics as metrics_routes
from app.presentation import well_known as well_known_routes
from app.presentation.webhooks import stripe as stripe_webhook
from app.services.activity import ActivityService
from app.services.agent_service import build_agent_service
from app.services.agents.provider_registry import get_provider_registry
from app.services.auth.builders import (
    build_service_account_token_service,
    build_session_service,
)
from app.services.auth_service import AuthService
from app.services.billing.payment_gateway import stripe_gateway
from app.services.geoip_service import build_geoip_service
from app.services.integrations.slack_notifier import build_slack_notifier
from app.services.signup.email_verification_service import build_email_verification_service
from app.services.signup.invite_service import build_invite_service
from app.services.signup.password_recovery_service import build_password_recovery_service
from app.services.signup.signup_request_service import build_signup_request_service
from app.services.signup.signup_service import build_signup_service
from app.services.status.status_alert_dispatcher import build_status_alert_dispatcher
from app.services.status.status_subscription_service import build_status_subscription_service
from app.services.usage_policy_service import build_usage_policy_service
from app.services.users import build_user_service
from app.services.vector_stores import (
    VectorLimitResolver,
    VectorStoreService,
    build_vector_store_sync_worker,
)

# =============================================================================
# MODULE CONSTANTS
# =============================================================================

logger = logging.getLogger(__name__)
_STRIPE_TROUBLESHOOTING_DOC = "docs/billing/stripe-setup.md#startup-validation--troubleshooting"
_PROVIDER_DOC = "docs/ops/provider-parity.md"


configure_logging(get_settings())

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


def _log_provider_violations(violations: list[ProviderViolation]) -> None:
    for violation in violations:
        log_fn = logger.error if violation.fatal else logger.warning
        log_fn(
            "Provider validation issue detected: %s (see %s)",
            violation.message,
            _PROVIDER_DOC,
            extra={
                "provider": violation.provider,
                "code": violation.code,
                "fatal": violation.fatal,
            },
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events."""
    settings = get_settings()
    provider_violations = validate_providers(settings)
    if provider_violations:
        _log_provider_violations(provider_violations)
    ensure_provider_parity(settings, violations=provider_violations)

    container = get_container()
    container.geoip_service = build_geoip_service(settings)
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
    enforce_vault_verification(settings)
    configure_vault_secret_manager(settings)

    stripe_repo: StripeEventRepository | None = None
    redis_factory = get_redis_factory(settings)

    rate_limit_url = settings.resolve_rate_limit_redis_url()
    if rate_limit_url:
        rate_limit_client = cast(
            RedisBytesClient,
            redis_factory.get_client("rate_limit"),
        )
        container.rate_limiter.configure(
            redis=rate_limit_client,
            prefix=settings.rate_limit_key_prefix,
            owns_client=False,
        )
    else:
        logger.warning(
            "Rate limiter disabled; RATE_LIMIT_REDIS_URL/REDIS_URL not configured.",
            extra={"environment": settings.environment},
        )

    if settings.enable_billing:
        _ensure_billing_prerequisites(settings)
        container.billing_service.set_gateway(stripe_gateway)

    run_migrations = settings.auto_run_migrations
    database_url = settings.database_url or ""
    if database_url.startswith("sqlite"):
        # SQLite test environments need schema bootstrap even when auto_run_migrations
        # is left at the default False.
        run_migrations = True

    await init_engine(run_migrations=run_migrations)
    engine = get_engine()
    if engine is None:
        raise RuntimeError("Database engine failed to initialise; cannot configure sessions.")
    session_factory = get_async_sessionmaker()
    container.session_factory = session_factory

    container.activity_service = ActivityService()
    activity_repo = SqlAlchemyActivityEventRepository(session_factory)
    container.activity_service.set_repository(activity_repo)
    activity_inbox_repo = SqlAlchemyActivityInboxRepository(session_factory)
    container.activity_service.set_inbox_repository(activity_inbox_repo)

    if settings.enable_activity_stream:
        redis_url = settings.resolve_activity_events_redis_url()
        if not redis_url:
            raise RuntimeError(
                "ENABLE_ACTIVITY_STREAM requires ACTIVITY_EVENTS_REDIS_URL or REDIS_URL"
            )
        activity_client = cast(
            RedisBytesClient,
            redis_factory.get_client("activity_events"),
        )
        activity_backend = RedisActivityEventBackend(
            activity_client,
            stream_max_length=settings.activity_stream_max_length,
            stream_ttl_seconds=settings.activity_stream_ttl_seconds,
            owns_client=False,
        )
        container.activity_service.set_stream_backend(activity_backend, enable=True)
    else:
        container.activity_service.set_stream_backend(None, enable=False)

    try:
        _ = container.conversation_service.repository
        repo_already_set = True
    except RuntimeError:
        repo_already_set = False

    if not repo_already_set:
        postgres_repository = PostgresConversationRepository(session_factory)
        container.conversation_service.set_repository(postgres_repository)
    container.tenant_settings_service.set_repository(
        PostgresTenantSettingsRepository(session_factory)
    )

    provider_registry = get_provider_registry()
    provider_registry.clear()
    provider_registry.register(
        build_openai_provider(
            settings_factory=lambda: settings,
            conversation_searcher=lambda tenant_id, query: container.conversation_service.search(
                tenant_id=tenant_id,
                query=query,
                limit=20,
            ),
            engine=engine,
        ),
        set_default=True,
    )

    user_repository = get_user_repository(settings)
    if user_repository is None:
        raise RuntimeError(
            "User repository is not configured. "
            "Run Postgres migrations and provide DATABASE_URL."
        )
    container.user_service = build_user_service(
        settings=settings,
        repository=user_repository,
    )

    container.user_session_service = build_session_service(
        settings=settings,
        user_service=container.user_service,
        geoip_service=container.geoip_service,
    )
    container.service_account_token_service = build_service_account_token_service(
        settings=settings,
    )

    refresh_repo = get_refresh_token_repository()
    session_repo = get_user_session_repository()
    container.auth_service = AuthService(
        refresh_repository=refresh_repo,
        session_repository=session_repo,
        user_service=container.user_service,
        geoip_service=container.geoip_service,
        session_service=container.user_session_service,
        service_account_service=container.service_account_token_service,
    )
    container.password_recovery_service = build_password_recovery_service(
        settings=settings,
        repository=user_repository,
        user_service=container.user_service,
    )
    container.email_verification_service = build_email_verification_service(
        settings=settings,
        repository=user_repository,
    )

    invite_repository = PostgresSignupInviteRepository(session_factory)
    request_repository = PostgresSignupRequestRepository(session_factory)
    container.invite_service = build_invite_service(
        repository=invite_repository,
        settings_factory=lambda: settings,
    )
    container.signup_request_service = build_signup_request_service(
        repository=request_repository,
        invite_service=container.invite_service,
        settings_factory=lambda: settings,
    )

    container.signup_service = build_signup_service(
        billing_service=container.billing_service if settings.enable_billing else None,
        auth_service=container.auth_service,
        email_verification_service=container.email_verification_service,
        settings_factory=lambda: settings,
        session_factory=session_factory,
        invite_service=container.invite_service,
    )

    status_repo = get_status_subscription_repository(settings)
    if status_repo:
        container.status_subscription_service = build_status_subscription_service(
            repository=status_repo,
            settings=settings,
        )
        slack_notifier = build_slack_notifier(settings)
        container.slack_notifier = slack_notifier
        container.status_alert_dispatcher = build_status_alert_dispatcher(
            repository=status_repo,
            settings=settings,
            slack_notifier=slack_notifier,
        )

    if settings.enable_billing:
        billing_service = container.billing_service
        billing_service.set_repository(PostgresBillingRepository(session_factory))
        container.usage_recorder.set_billing_service(billing_service)
        usage_cache_backend = settings.usage_guardrail_cache_backend
        usage_cache_client = None
        if usage_cache_backend == "redis":
            try:
                usage_cache_client = cast(
                    RedisBytesClient,
                    redis_factory.get_client("usage_cache"),
                )
            except RuntimeError as exc:
                logger.warning(
                    "Usage guardrail cache backend set to redis but no Redis URL configured; "
                    "falling back to in-memory cache.",
                    extra={"environment": settings.environment},
                    exc_info=exc,
                )
                usage_cache_backend = "memory"
        if settings.enable_usage_guardrails:
            container.usage_policy_service = build_usage_policy_service(
                billing_service=billing_service,
                cache_ttl_seconds=settings.usage_guardrail_cache_ttl_seconds,
                soft_limit_mode=settings.usage_guardrail_soft_limit_mode,
                cache_backend=usage_cache_backend,
                redis_client=usage_cache_client,
            )
        else:
            container.usage_policy_service = None
        stripe_repo = StripeEventRepository(session_factory)
        configure_stripe_event_repository(stripe_repo)
        container.stripe_event_dispatcher.configure(repository=stripe_repo, billing=billing_service)
        container.billing_events_service.configure(repository=stripe_repo)
        if settings.enable_billing_retry_worker:
            worker = container.stripe_dispatch_retry_worker
            worker.configure(
                repository=stripe_repo, dispatcher=container.stripe_event_dispatcher
            )
            await worker.start()
        else:
            logger.info("Stripe dispatch retry worker disabled by configuration")

        if settings.enable_billing_stream:
            redis_url = settings.resolve_billing_events_redis_url()
            if not redis_url:
                raise RuntimeError(
                    "ENABLE_BILLING_STREAM requires BILLING_EVENTS_REDIS_URL or REDIS_URL"
                )
            redis_client = cast(
                RedisBytesClient,
                redis_factory.get_client("billing_events"),
            )
            backend = RedisBillingEventBackend(redis_client, owns_client=False)
            service = container.billing_events_service
            service.configure(backend=backend)
            if settings.enable_billing_stream_replay:
                await service.startup()
            else:
                logger.info("Billing stream replay/startup disabled by configuration")
        # Vector limits resolver (plan-aware)
        container.vector_limit_resolver = VectorLimitResolver(
            billing_service=billing_service,
            settings_factory=lambda: settings,
        )
    else:
        container.usage_policy_service = None
        container.vector_limit_resolver = None

    # Vector store service (OpenAI vector stores + file search)
    container.vector_store_service = VectorStoreService(
        session_factory,
        get_settings,
        limit_resolver=container.vector_limit_resolver,
    )

    # Agent service (after vector store is finalized)
    wire_title_service(container)
    container.agent_service = build_agent_service(
        conversation_service=container.conversation_service,
        usage_recorder=container.usage_recorder,
        provider_registry=provider_registry,
        container_service=container.container_service,
        vector_store_service=container.vector_store_service,
        title_service=container.title_service,
    )

    # Conversation query service (history + search) wired once at startup
    wire_conversation_query_service(container)

    # Optional background sync worker
    if settings.enable_vector_store_sync_worker:
        if container.vector_store_service is None:
            raise RuntimeError("Vector store service failed to initialize")
        container.vector_store_sync_worker = build_vector_store_sync_worker(
            session_factory=session_factory,
            settings_factory=lambda: settings,
            client_factory=container.vector_store_service.openai_client,
        )
        await container.vector_store_sync_worker.start()
    try:
        yield
    finally:
        await shutdown_container()
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
    app.include_router(api_router, prefix="/api")

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
