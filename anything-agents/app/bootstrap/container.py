"""Centralized application dependency container."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from app.services.auth.service_account_service import ServiceAccountTokenService
from app.services.auth.session_service import UserSessionService
from app.services.billing_events import BillingEventsService
from app.services.billing_service import BillingService
from app.services.conversation_service import ConversationService
from app.services.email_verification_service import EmailVerificationService
from app.services.geoip_service import GeoIPService, NullGeoIPService
from app.services.password_recovery_service import PasswordRecoveryService
from app.services.rate_limit_service import RateLimiter
from app.services.stripe_dispatcher import StripeEventDispatcher
from app.services.stripe_retry_worker import StripeDispatchRetryWorker
from app.services.user_service import UserService

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from app.infrastructure.persistence.stripe.repository import StripeEventRepository
    from app.services.agent_service import AgentService
    from app.services.auth_service import AuthService
    from app.services.signup_service import SignupService


@dataclass(slots=True)
class ApplicationContainer:
    """Holds long-lived application services and infrastructure handles."""

    session_factory: async_sessionmaker[AsyncSession] | None = None
    conversation_service: ConversationService = field(default_factory=ConversationService)
    billing_service: BillingService = field(default_factory=BillingService)
    billing_events_service: BillingEventsService = field(default_factory=BillingEventsService)
    rate_limiter: RateLimiter = field(default_factory=RateLimiter)
    stripe_event_dispatcher: StripeEventDispatcher = field(
        default_factory=StripeEventDispatcher
    )
    stripe_dispatch_retry_worker: StripeDispatchRetryWorker = field(
        default_factory=StripeDispatchRetryWorker
    )
    stripe_event_repository: StripeEventRepository | None = None
    user_service: UserService | None = None
    geoip_service: GeoIPService = field(default_factory=NullGeoIPService)
    auth_service: AuthService | None = None
    password_recovery_service: PasswordRecoveryService | None = None
    email_verification_service: EmailVerificationService | None = None
    user_session_service: UserSessionService | None = None
    service_account_token_service: ServiceAccountTokenService | None = None
    agent_service: AgentService | None = None
    signup_service: SignupService | None = None

    async def shutdown(self) -> None:
        """Gracefully tear down managed services."""

        await asyncio.gather(
            self.billing_events_service.shutdown(),
            self.stripe_dispatch_retry_worker.shutdown(),
            self.rate_limiter.shutdown(),
            return_exceptions=False,
        )
        self.session_factory = None
        self.stripe_event_repository = None
        self.user_service = None
        self.auth_service = None
        self.password_recovery_service = None
        self.email_verification_service = None
        self.user_session_service = None
        self.service_account_token_service = None
        self.agent_service = None
        self.signup_service = None


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

    container = ApplicationContainer()
    set_container(container)
    return container


__all__ = [
    "ApplicationContainer",
    "get_container",
    "reset_container",
    "set_container",
    "shutdown_container",
]
