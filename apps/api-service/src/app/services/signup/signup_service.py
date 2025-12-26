"""Self-serve signup orchestration across tenants, users, and billing."""

from __future__ import annotations

import logging
import re
import secrets
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.password_policy import PasswordPolicyError, validate_password_strength
from app.core.security import PASSWORD_HASH_VERSION, get_password_hash
from app.core.settings import Settings, get_settings
from app.infrastructure.db import get_async_sessionmaker
from app.infrastructure.persistence.auth.models.membership import TenantUserMembership
from app.infrastructure.persistence.auth.models.user import (
    PasswordHistory,
    UserAccount,
    UserProfile,
    UserStatus,
)
from app.infrastructure.persistence.tenants.models import TenantAccount
from app.observability.logging import log_event
from app.services.activity import activity_service
from app.services.auth_service import AuthService, UserSessionTokens, get_auth_service
from app.services.billing.billing_service import (
    BillingError,
    BillingService,
    PaymentProviderError,
    get_billing_service,
)
from app.services.signup.email_verification_service import (
    EmailVerificationService,
    get_email_verification_service,
)
from app.services.signup.invite_service import (
    InviteEmailMismatchError,
    InviteExpiredError,
    InviteNotFoundError,
    InviteRequestMismatchError,
    InviteReservationContext,
    InviteRevokedError,
    InviteService,
    InviteTokenRequiredError,
    get_invite_service,
)

SlugGenerator = Callable[[str], str]

logger = logging.getLogger(__name__)


class SignupServiceError(RuntimeError):
    """Base error for signup orchestration."""


class PublicSignupDisabledError(SignupServiceError):
    """Raised when public signup is disabled via configuration."""


class TenantSlugCollisionError(SignupServiceError):
    """Raised when a tenant slug cannot be provisioned."""


class EmailAlreadyRegisteredError(SignupServiceError):
    """Raised when the supplied email already exists."""


class BillingProvisioningError(SignupServiceError):
    """Raised when billing fails during signup."""


@dataclass(slots=True)
class SignupResult:
    tenant_id: str
    tenant_slug: str
    user_id: str
    session: UserSessionTokens


class SignupService:
    """Co-ordinates tenant creation, owner provisioning, and optional billing."""

    def __init__(
        self,
        *,
        billing: BillingService | None = None,
        settings_factory: Callable[[], Settings] | None = None,
        slug_generator: SlugGenerator | None = None,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        auth: AuthService | None = None,
        email_verification_service: EmailVerificationService | None = None,
        invite_service: InviteService | None = None,
    ) -> None:
        self._billing_service = billing
        self._settings_factory = settings_factory or get_settings
        self._slug_generator = slug_generator or self._default_slugify
        self._session_factory = session_factory
        self._auth_service = auth
        self._email_verification_service = email_verification_service
        self._invite_service = invite_service

    def _get_settings(self) -> Settings:
        return self._settings_factory()

    def _get_auth_service(self) -> AuthService:
        if self._auth_service is None:
            self._auth_service = get_auth_service()
        return self._auth_service

    def _get_email_verification_service(self) -> EmailVerificationService:
        if self._email_verification_service is None:
            self._email_verification_service = get_email_verification_service()
        return self._email_verification_service

    def _get_invite_service(self) -> InviteService:
        if self._invite_service is None:
            self._invite_service = get_invite_service()
        return self._invite_service

    def _get_billing_service(self) -> BillingService | None:
        if self._billing_service is None:
            try:
                self._billing_service = get_billing_service()
            except RuntimeError:
                self._billing_service = None
        return self._billing_service

    async def register(
        self,
        *,
        email: str,
        password: str,
        tenant_name: str,
        display_name: str | None,
        plan_code: str | None,
        trial_days: int | None,
        ip_address: str | None,
        user_agent: str | None,
        invite_token: str | None,
    ) -> SignupResult:
        settings = self._get_settings()
        invite_context: InviteReservationContext | None = None
        if settings.signup_access_policy != "public":
            invite_context = await self._reserve_invite_context(
                policy=settings.signup_access_policy,
                invite_token=invite_token,
                email=email,
            )

        try:
            try:
                validate_password_strength(password, user_inputs=[email])
            except PasswordPolicyError as exc:
                raise SignupServiceError(str(exc)) from exc

            tenant_slug = await self._ensure_unique_slug(self._slug_generator(tenant_name))
            tenant_id, user_id = await self._provision_tenant_owner(
                tenant_name=tenant_name.strip(),
                tenant_slug=tenant_slug,
                email=email,
                password=password,
                display_name=display_name,
            )

            resolved_plan = plan_code or settings.signup_default_plan_code
            await self._maybe_provision_subscription(
                tenant_id=tenant_id,
                plan_code=resolved_plan,
                billing_email=email,
                requested_trial_days=trial_days,
            )

            tokens = await self._get_auth_service().login_user(
                email=email,
                password=password,
                tenant_id=tenant_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            await self._trigger_email_verification(
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            log_event(
                "signup.completed",
                result="success",
                tenant_id=tenant_id,
                tenant_slug=tenant_slug,
                plan_code=resolved_plan or "none",
                invite_id=str(invite_context.invite.id) if invite_context else None,
            )

            try:
                await activity_service.record(
                    tenant_id=str(tenant_id),
                    action="auth.signup.success",
                    actor_id=str(user_id),
                    actor_type="user",
                    object_type="tenant",
                    object_id=str(tenant_id),
                    source="api",
                    user_agent=user_agent,
                    ip_address=ip_address,
                    metadata={"user_id": str(user_id), "tenant_id": str(tenant_id)},
                )
            except Exception:  # pragma: no cover - best effort
                logger.debug("activity.log.signup.skipped", exc_info=True)

            if invite_context:
                await invite_context.mark_succeeded(tenant_id=tenant_id, user_id=user_id)

            return SignupResult(
                tenant_id=tenant_id,
                tenant_slug=tenant_slug,
                user_id=user_id,
                session=tokens,
            )
        except Exception:
            await self._register_cleanup(invite_context, reason="signup_failed")
            raise
        finally:
            await self._register_cleanup(invite_context, reason="signup_abandoned")

    async def _register_cleanup(
        self,
        invite_context: InviteReservationContext | None,
        *,
        reason: str,
    ) -> None:
        if invite_context is None:
            return
        await invite_context.ensure_released(reason=reason)

    async def _trigger_email_verification(
        self,
        *,
        user_id: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        try:
            service = self._get_email_verification_service()
            await service.send_verification_email(
                user_id=user_id,
                email=None,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except Exception as exc:  # pragma: no cover - best effort
            log_event(
                "signup.email_verification",
                result="error",
                user_id=user_id,
                reason=str(exc),
            )

    async def _ensure_unique_slug(self, base_slug: str) -> str:
        candidate = base_slug
        attempts = 0
        while await self._slug_exists(candidate):
            attempts += 1
            suffix = secrets.token_hex(2)
            trimmed = base_slug[: max(16, 60 - len(suffix) - 1)]
            candidate = f"{trimmed}-{suffix}"
            if attempts > 10:
                raise TenantSlugCollisionError("Unable to allocate a unique tenant slug.")
        return candidate

    async def _slug_exists(self, slug: str) -> bool:
        session_factory = self._get_session_factory()
        async with session_factory() as session:
            result = await session.execute(
                select(TenantAccount.id).where(TenantAccount.slug == slug).limit(1)
            )
            return result.scalar_one_or_none() is not None

    async def _provision_tenant_owner(
        self,
        *,
        tenant_name: str,
        tenant_slug: str,
        email: str,
        password: str,
        display_name: str | None,
    ) -> tuple[str, str]:
        normalized_email = email.strip().lower()
        hashed_password = get_password_hash(password)
        session_factory = self._get_session_factory()
        async with session_factory() as session:
            try:
                async with session.begin():
                    existing_user = await session.scalar(
                        select(UserAccount.id).where(UserAccount.email == normalized_email)
                    )
                    if existing_user:
                        raise EmailAlreadyRegisteredError("Email already registered.")

                    tenant_id = uuid.uuid4()
                    user_id = uuid.uuid4()

                    tenant = TenantAccount(id=tenant_id, slug=tenant_slug, name=tenant_name)
                    session.add(tenant)

                    user = UserAccount(
                        id=user_id,
                        email=normalized_email,
                        password_hash=hashed_password,
                        password_pepper_version=PASSWORD_HASH_VERSION,
                        status=UserStatus.ACTIVE,
                    )
                    session.add(user)

                    if display_name:
                        session.add(
                            UserProfile(
                                id=uuid.uuid4(),
                                user_id=user_id,
                                display_name=display_name,
                            )
                        )

                    session.add(
                        TenantUserMembership(
                            id=uuid.uuid4(),
                            user_id=user_id,
                            tenant_id=tenant_id,
                            role="owner",
                        )
                    )

                    session.add(
                        PasswordHistory(
                            id=uuid.uuid4(),
                            user_id=user_id,
                            password_hash=hashed_password,
                            password_pepper_version=PASSWORD_HASH_VERSION,
                            created_at=datetime.now(UTC),
                        )
                    )

                return str(tenant_id), str(user_id)
            except EmailAlreadyRegisteredError:
                raise
            except IntegrityError as exc:  # pragma: no cover - rare slug race
                raise TenantSlugCollisionError("Tenant slug already exists.") from exc

    async def _maybe_provision_subscription(
        self,
        *,
        tenant_id: str,
        plan_code: str | None,
        billing_email: str,
        requested_trial_days: int | None,
    ) -> None:
        settings = self._get_settings()
        if not plan_code or not settings.enable_billing:
            # Billing disabled or no plan requested; record telemetry only.
            log_event(
                "signup.billing_skipped",
                result="skipped",
                tenant_id=tenant_id,
                reason="billing_disabled" if not settings.enable_billing else "plan_missing",
            )
            return

        service = self._get_billing_service()
        if service is None:
            raise BillingProvisioningError("Billing service is not configured.")

        trial_days = await self._select_trial_days(
            plan_code=plan_code,
            requested_trial_days=requested_trial_days,
        )
        try:
            await service.start_subscription(
                tenant_id=tenant_id,
                plan_code=plan_code,
                billing_email=billing_email,
                auto_renew=True,
                seat_count=1,
                trial_days=trial_days,
            )
        except PaymentProviderError as exc:
            raise BillingProvisioningError(str(exc)) from exc
        except BillingError:
            raise
        else:
            log_event(
                "signup.billing_provisioned",
                result="success",
                tenant_id=tenant_id,
                plan_code=plan_code,
                trial_days=trial_days,
            )

    async def _select_trial_days(
        self,
        *,
        plan_code: str | None,
        requested_trial_days: int | None,
    ) -> int | None:
        settings = self._get_settings()
        plan_trial_days = await self._lookup_plan_trial_days(plan_code)
        max_allowed: int | None
        if plan_trial_days is not None:
            max_allowed = plan_trial_days
        else:
            max_allowed = settings.signup_default_trial_days
        max_allowed = max_allowed if max_allowed and max_allowed > 0 else None

        if not settings.allow_signup_trial_override or requested_trial_days is None:
            return max_allowed

        cap = max_allowed if max_allowed is not None else 0
        candidate = min(requested_trial_days, cap)
        return candidate if candidate and candidate > 0 else None

    async def _lookup_plan_trial_days(self, plan_code: str | None) -> int | None:
        if not plan_code:
            return None
        service = self._get_billing_service()
        if service is None:
            return None
        try:
            plans = await service.list_plans()
        except BillingError as exc:
            log_event(
                "signup.plan_lookup_failed",
                result="error",
                plan_code=plan_code,
                error=str(exc),
            )
            return None

        for plan in plans:
            if plan.code == plan_code:
                return plan.trial_days
        return None

    def _get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            self._session_factory = get_async_sessionmaker()
        return self._session_factory

    async def _reserve_invite_context(
        self,
        *,
        policy: str,
        invite_token: str | None,
        email: str,
    ):
        if policy == "public":  # pragma: no cover - guard
            return None
        try:
            context = await self._get_invite_service().reserve_for_signup(
                token=invite_token,
                email=email,
                require_request=policy == "approval",
            )
        except InviteTokenRequiredError as exc:
            raise PublicSignupDisabledError(str(exc)) from exc
        except InviteExpiredError as exc:
            raise PublicSignupDisabledError(str(exc)) from exc
        except InviteRequestMismatchError as exc:
            raise PublicSignupDisabledError(str(exc)) from exc
        except InviteRevokedError as exc:
            raise PublicSignupDisabledError(str(exc)) from exc
        except InviteNotFoundError as exc:
            raise PublicSignupDisabledError(str(exc)) from exc
        except InviteEmailMismatchError as exc:
            raise PublicSignupDisabledError(str(exc)) from exc
        return context

    @staticmethod
    def _default_slugify(value: str) -> str:
        normalized = value.strip().lower()
        normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
        return normalized[:60] or "tenant"

def build_signup_service(
    *,
    billing_service: BillingService | None = None,
    auth_service: AuthService | None = None,
    email_verification_service: EmailVerificationService | None = None,
    settings_factory: Callable[[], Settings] | None = None,
    slug_generator: SlugGenerator | None = None,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    invite_service: InviteService | None = None,
) -> SignupService:
    return SignupService(
        billing=billing_service,
        settings_factory=settings_factory,
        slug_generator=slug_generator,
        session_factory=session_factory,
        auth=auth_service,
        email_verification_service=email_verification_service,
        invite_service=invite_service,
    )


def get_signup_service() -> SignupService:
    from app.bootstrap.container import get_container

    container = get_container()
    if container.signup_service is None:
        container.signup_service = build_signup_service()
    return container.signup_service


class _SignupServiceHandle:
    def __getattr__(self, name: str):
        return getattr(get_signup_service(), name)

    def __setattr__(self, name: str, value):
        setattr(get_signup_service(), name, value)

    def __delattr__(self, name: str):
        delattr(get_signup_service(), name)


signup_service = _SignupServiceHandle()


__all__ = [
    "BillingProvisioningError",
    "EmailAlreadyRegisteredError",
    "SignupServiceError",
    "PublicSignupDisabledError",
    "SignupResult",
    "SignupService",
    "TenantSlugCollisionError",
    "build_signup_service",
    "get_signup_service",
    "signup_service",
]
