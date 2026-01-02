"""Self-serve signup orchestration across tenants, users, and billing."""

from __future__ import annotations

import logging
from collections.abc import Callable

from app.core.password_policy import PasswordPolicyError, validate_password_strength
from app.core.settings import Settings, get_settings
from app.services.auth_service import AuthService, get_auth_service
from app.services.billing.billing_service import BillingService
from app.services.signup.billing import SignupBillingService
from app.services.signup.contracts import SignupCommand, SignupResult
from app.services.signup.email_verification_service import EmailVerificationService
from app.services.signup.errors import (
    BillingProvisioningError,
    EmailAlreadyRegisteredError,
    PublicSignupDisabledError,
    SignupServiceError,
    TenantSlugCollisionError,
)
from app.services.signup.invite_policy import SignupInvitePolicyService
from app.services.signup.invite_service import InviteReservationContext, InviteService
from app.services.signup.notifications import SignupNotificationService
from app.services.signup.provisioning import SignupProvisioningService
from app.services.signup.telemetry import SignupTelemetry
from app.services.tenant.tenant_account_service import TenantAccountService

logger = logging.getLogger(__name__)


class SignupService:
    """Co-ordinates tenant creation, owner provisioning, and optional billing."""

    def __init__(
        self,
        *,
        billing: BillingService | None = None,
        settings_factory: Callable[[], Settings] | None = None,
        session_factory=None,
        auth: AuthService | None = None,
        email_verification_service: EmailVerificationService | None = None,
        invite_service: InviteService | None = None,
        tenant_account_service: TenantAccountService | None = None,
    ) -> None:
        self._billing_service = billing
        self._settings_factory = settings_factory or get_settings
        self._session_factory = session_factory
        self._auth_service = auth
        self._email_verification_service = email_verification_service
        self._invite_service = invite_service
        self._tenant_account_service = tenant_account_service
        self._billing = None
        self._invite_policy = None
        self._notifications = None
        self._provisioning = None
        self._telemetry = None

    def _get_settings(self) -> Settings:
        return self._settings_factory()

    def _get_auth_service(self) -> AuthService:
        if self._auth_service is None:
            self._auth_service = get_auth_service()
        return self._auth_service

    def _get_billing(self) -> SignupBillingService:
        if self._billing is None:
            self._billing = SignupBillingService(
                billing_service=self._billing_service,
                settings_factory=self._settings_factory,
            )
        return self._billing

    def _get_invite_policy(self) -> SignupInvitePolicyService:
        if self._invite_policy is None:
            self._invite_policy = SignupInvitePolicyService(
                invite_service=self._invite_service,
                settings_factory=self._settings_factory,
            )
        return self._invite_policy

    def _get_notifications(self) -> SignupNotificationService:
        if self._notifications is None:
            self._notifications = SignupNotificationService(
                email_verification=self._email_verification_service
            )
        return self._notifications

    def _get_provisioning(self) -> SignupProvisioningService:
        if self._provisioning is None:
            self._provisioning = SignupProvisioningService(
                session_factory=self._session_factory,
                tenant_account_service=self._tenant_account_service,
            )
        return self._provisioning

    def _get_telemetry(self) -> SignupTelemetry:
        if self._telemetry is None:
            self._telemetry = SignupTelemetry()
        return self._telemetry

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
        command = SignupCommand(
            email=email,
            password=password,
            tenant_name=tenant_name,
            display_name=display_name,
            plan_code=plan_code,
            trial_days=trial_days,
            ip_address=ip_address,
            user_agent=user_agent,
            invite_token=invite_token,
        )
        return await self._register(command)

    async def _register(self, command: SignupCommand) -> SignupResult:
        settings = self._get_settings()
        invite_context = await self._get_invite_policy().reserve_if_required(
            email=command.email,
            invite_token=command.invite_token,
        )

        try:
            try:
                validate_password_strength(command.password, user_inputs=[command.email])
            except PasswordPolicyError as exc:
                raise SignupServiceError(str(exc)) from exc

            provisioning = self._get_provisioning()
            provisioned = await provisioning.provision_tenant_owner(
                tenant_name=command.tenant_name,
                email=command.email,
                password=command.password,
                display_name=command.display_name,
            )

            resolved_plan = command.plan_code or settings.signup_default_plan_code
            try:
                await self._get_billing().provision_subscription_if_needed(
                    tenant_id=str(provisioned.tenant_id),
                    plan_code=resolved_plan,
                    billing_email=command.email,
                    requested_trial_days=command.trial_days,
                )
            except Exception:
                try:
                    await provisioning.fail_provisioning(
                        tenant_id=provisioned.tenant_id,
                        user_id=provisioned.user_id,
                        reason="signup_billing_failed",
                    )
                except Exception:  # pragma: no cover - best effort cleanup
                    logger.warning(
                        "signup.provisioning_cleanup_failed",
                        exc_info=True,
                        extra={
                            "tenant_id": str(provisioned.tenant_id),
                            "user_id": str(provisioned.user_id),
                        },
                    )
                raise

            await provisioning.finalize_provisioning(
                tenant_id=provisioned.tenant_id,
                user_id=provisioned.user_id,
                reason="signup_completed",
            )

            tokens = await self._get_auth_service().login_user(
                email=command.email,
                password=command.password,
                tenant_id=str(provisioned.tenant_id),
                ip_address=command.ip_address,
                user_agent=command.user_agent,
            )

            await self._get_notifications().send_email_verification(
                user_id=str(provisioned.user_id),
                ip_address=command.ip_address,
                user_agent=command.user_agent,
            )

            await self._get_telemetry().record_signup_success(
                tenant_id=str(provisioned.tenant_id),
                tenant_slug=provisioned.tenant_slug,
                user_id=str(provisioned.user_id),
                plan_code=resolved_plan,
                invite_id=str(invite_context.invite.id) if invite_context else None,
                user_agent=command.user_agent,
                ip_address=command.ip_address,
            )

            if invite_context:
                await invite_context.mark_succeeded(
                    tenant_id=str(provisioned.tenant_id),
                    user_id=provisioned.user_id,
                )

            return SignupResult(
                tenant_id=str(provisioned.tenant_id),
                tenant_slug=provisioned.tenant_slug,
                user_id=str(provisioned.user_id),
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


def build_signup_service(
    *,
    billing_service: BillingService | None = None,
    auth_service: AuthService | None = None,
    email_verification_service: EmailVerificationService | None = None,
    settings_factory: Callable[[], Settings] | None = None,
    session_factory=None,
    invite_service: InviteService | None = None,
    tenant_account_service: TenantAccountService | None = None,
) -> SignupService:
    return SignupService(
        billing=billing_service,
        settings_factory=settings_factory,
        session_factory=session_factory,
        auth=auth_service,
        email_verification_service=email_verification_service,
        invite_service=invite_service,
        tenant_account_service=tenant_account_service,
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
    "PublicSignupDisabledError",
    "SignupResult",
    "SignupService",
    "SignupServiceError",
    "TenantSlugCollisionError",
    "build_signup_service",
    "get_signup_service",
    "signup_service",
]
