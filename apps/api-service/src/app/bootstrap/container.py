"""Centralized application dependency container."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, cast

from app.core.settings import get_settings
from app.infrastructure.persistence.workflows.repository import (
    SqlAlchemyWorkflowRunRepository,
)
from app.infrastructure.redis.factory import reset_redis_factory, shutdown_redis_factory
from app.services.activity import ActivityService
from app.services.agents.interaction_context import InteractionContextBuilder
from app.services.auth.service_account_service import ServiceAccountTokenService
from app.services.auth.session_service import UserSessionService
from app.services.billing.billing_events import BillingEventsService
from app.services.billing.billing_service import BillingService
from app.services.billing.stripe.dispatcher import StripeEventDispatcher
from app.services.billing.stripe.retry_worker import StripeDispatchRetryWorker
from app.services.contact_service import ContactService
from app.services.containers import ContainerService
from app.services.conversation_service import ConversationService
from app.services.geoip_service import GeoIPService, NullGeoIPService, shutdown_geoip_service
from app.services.integrations.slack_notifier import SlackNotifier
from app.services.shared.rate_limit_service import RateLimiter
from app.services.signup.email_verification_service import EmailVerificationService
from app.services.signup.password_recovery_service import PasswordRecoveryService
from app.services.status.status_alert_dispatcher import StatusAlertDispatcher
from app.services.status.status_subscription_service import StatusSubscriptionService
from app.services.storage.service import StorageService
from app.services.tenant.tenant_settings_service import TenantSettingsService
from app.services.usage_policy_service import UsagePolicyService
from app.services.usage_recorder import UsageRecorder
from app.services.users import UserService
from app.services.vector_stores import (
    VectorLimitResolver,
    VectorStoreService,
    VectorStoreSyncWorker,
)
from app.services.workflows.service import WorkflowService

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from app.infrastructure.persistence.stripe.repository import StripeEventRepository
    from app.services.agent_service import AgentService
    from app.services.agents.query import ConversationQueryService
    from app.services.auth_service import AuthService
    from app.services.signup.invite_service import InviteService
    from app.services.signup.signup_request_service import SignupRequestService
    from app.services.signup.signup_service import SignupService


@dataclass(slots=True)
class ApplicationContainer:
    """Holds long-lived application services and infrastructure handles."""

    session_factory: async_sessionmaker[AsyncSession] | None = None
    conversation_service: ConversationService = field(default_factory=ConversationService)
    billing_service: BillingService = field(default_factory=BillingService)
    billing_events_service: BillingEventsService = field(default_factory=BillingEventsService)
    activity_service: ActivityService | None = None
    rate_limiter: RateLimiter = field(default_factory=RateLimiter)
    stripe_event_dispatcher: StripeEventDispatcher = field(
        default_factory=StripeEventDispatcher
    )
    stripe_dispatch_retry_worker: StripeDispatchRetryWorker = field(
        default_factory=StripeDispatchRetryWorker
    )
    stripe_event_repository: StripeEventRepository | None = None
    user_service: UserService | None = None
    contact_service: ContactService | None = None
    geoip_service: GeoIPService = field(default_factory=NullGeoIPService)
    slack_notifier: SlackNotifier | None = None
    auth_service: AuthService | None = None
    password_recovery_service: PasswordRecoveryService | None = None
    email_verification_service: EmailVerificationService | None = None
    user_session_service: UserSessionService | None = None
    service_account_token_service: ServiceAccountTokenService | None = None
    agent_service: AgentService | None = None
    signup_service: SignupService | None = None
    invite_service: InviteService | None = None
    signup_request_service: SignupRequestService | None = None
    status_subscription_service: StatusSubscriptionService | None = None
    status_alert_dispatcher: StatusAlertDispatcher | None = None
    tenant_settings_service: TenantSettingsService = field(
        default_factory=TenantSettingsService
    )
    conversation_query_service: ConversationQueryService | None = None
    vector_limit_resolver: VectorLimitResolver | None = None
    vector_store_service: VectorStoreService | None = None
    vector_store_sync_worker: VectorStoreSyncWorker | None = None
    container_service: ContainerService | None = None
    usage_recorder: UsageRecorder = field(default_factory=UsageRecorder)
    usage_policy_service: UsagePolicyService | None = None
    storage_service: StorageService | None = None
    workflow_run_repository: SqlAlchemyWorkflowRunRepository | None = None
    workflow_service: WorkflowService | None = None

    async def shutdown(self) -> None:
        """Gracefully tear down managed services."""

        await asyncio.gather(
            self.billing_events_service.shutdown(),
            self.stripe_dispatch_retry_worker.shutdown(),
            *(
                [self.vector_store_sync_worker.shutdown()] if self.vector_store_sync_worker else []
            ),
            self.rate_limiter.shutdown(),
            return_exceptions=False,
        )
        if self.slack_notifier:
            await self.slack_notifier.shutdown()
        await shutdown_geoip_service(self.geoip_service)
        await shutdown_redis_factory()
        self.session_factory = None
        self.stripe_event_repository = None
        self.user_service = None
        self.auth_service = None
        self.password_recovery_service = None
        self.email_verification_service = None
        self.user_session_service = None
        self.service_account_token_service = None
        self.contact_service = None
        self.agent_service = None
        self.conversation_query_service = None
        self.signup_service = None
        self.invite_service = None
        self.signup_request_service = None
        self.status_subscription_service = None
        self.status_alert_dispatcher = None
        self.geoip_service = NullGeoIPService()
        self.usage_policy_service = None
        self.vector_store_sync_worker = None
        self.container_service = None


_CONTAINER: ApplicationContainer | None = None


def get_container() -> ApplicationContainer:
    """Return the active container, creating a default one if needed."""

    global _CONTAINER
    if _CONTAINER is None:
        _CONTAINER = ApplicationContainer()
    return _CONTAINER


def set_container(container: ApplicationContainer) -> ApplicationContainer:
    """Install a fully configured container (used during startup)."""

    global _CONTAINER
    _CONTAINER = container
    return _CONTAINER


async def shutdown_container() -> None:
    """Shutdown and clear the active container."""

    global _CONTAINER
    if _CONTAINER is None:
        return
    await _CONTAINER.shutdown()
    _CONTAINER = None


def reset_container() -> ApplicationContainer:
    """Reset the container to a fresh, unconfigured instance (used in tests)."""

    reset_redis_factory()
    container = ApplicationContainer()
    set_container(container)
    return container


def wire_vector_store_service(container: ApplicationContainer) -> None:
    """Initialize the vector store service using the shared session factory."""

    if container.vector_store_service is None:
        if container.session_factory is None:
            raise RuntimeError("Session factory must be configured before vector store service")
        settings = get_settings()
        container.vector_store_service = VectorStoreService(
            container.session_factory,
            lambda: settings,
            limit_resolver=container.vector_limit_resolver,
        )


def wire_container_service(container: ApplicationContainer) -> None:
    """Initialize the container service using the shared session factory."""

    if container.container_service is None:
        if container.session_factory is None:
            raise RuntimeError("Session factory must be configured before container service")
        settings = get_settings()
        container.container_service = ContainerService(
            container.session_factory,
            lambda: settings,
        )


def wire_storage_service(container: ApplicationContainer) -> None:
    """Initialize the storage service using the shared session factory."""

    if container.storage_service is None:
        if container.session_factory is None:
            raise RuntimeError("Session factory must be configured before storage service")
        settings = get_settings()
        container.storage_service = StorageService(
            container.session_factory,
            lambda: settings,
        )


def wire_conversation_query_service(container: ApplicationContainer) -> None:
    """Initialize the conversation query service with history + attachments."""

    if container.conversation_query_service is not None:
        return
    if container.storage_service is None:
        wire_storage_service(container)
    if container.storage_service is None:
        raise RuntimeError("Storage service must be configured before conversation query service")

    from app.services.agents.attachments import AttachmentService
    from app.services.agents.history import ConversationHistoryService
    from app.services.agents.query import ConversationQueryService

    storage_service = cast(StorageService, container.storage_service)
    history_service = ConversationHistoryService(
        container.conversation_service,
        AttachmentService(lambda: storage_service),
    )
    container.conversation_query_service = ConversationQueryService(
        conversation_service=container.conversation_service,
        history_service=history_service,
    )


def wire_workflow_services(container: ApplicationContainer) -> None:
    if container.session_factory is None:
        raise RuntimeError("Session factory must be configured before workflow services")

    if container.vector_store_service is None:
        wire_vector_store_service(container)

    if container.workflow_run_repository is None:
        container.workflow_run_repository = SqlAlchemyWorkflowRunRepository(
            container.session_factory
        )

    if container.workflow_service is None:
        container.workflow_service = WorkflowService(
            registry=None,
            provider_registry=None,
            interaction_builder=InteractionContextBuilder(
                container_service=container.container_service,
                vector_store_service=container.vector_store_service,
            ),
            run_repository=container.workflow_run_repository,
        )


__all__ = [
    "ApplicationContainer",
    "get_container",
    "reset_container",
    "set_container",
    "shutdown_container",
    "wire_vector_store_service",
    "wire_container_service",
    "wire_storage_service",
    "wire_conversation_query_service",
    "wire_workflow_services",
    "VectorLimitResolver",
    "VectorStoreSyncWorker",
]
