"""SSO provisioning policies and membership orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app.domain.sso import SsoAutoProvisionPolicy
from app.domain.team import TenantMembershipRepository
from app.domain.tenant_roles import TenantRole
from app.domain.users import UserRecord
from app.observability.logging import log_event
from app.services.team.acceptance_service import (
    TeamInviteAcceptanceService,
    TeamInviteInvalidError,
    TeamInviteRequiredError,
)
from app.services.users.provisioning import (
    UserProvisioningRequest,
    UserProvisioningService,
)

from .config import email_domain_allowed
from .errors import SsoProvisioningError


@dataclass(slots=True)
class SsoProvisioningInput:
    user: UserRecord | None
    tenant_id: UUID
    policy: SsoAutoProvisionPolicy
    allowed_domains: list[str]
    default_role: TenantRole
    email: str | None
    email_verified: bool
    display_name: str | None
    now: datetime | None = None


class SsoProvisioner:
    def __init__(
        self,
        *,
        membership_repository: TenantMembershipRepository,
        invite_acceptance_service: TeamInviteAcceptanceService,
        user_provisioning_service: UserProvisioningService,
    ) -> None:
        self._membership_repository = membership_repository
        self._invite_acceptance_service = invite_acceptance_service
        self._user_provisioning_service = user_provisioning_service

    async def ensure_membership(self, *, payload: SsoProvisioningInput) -> UserRecord:
        if payload.user is not None and await self._membership_repository.membership_exists(
            tenant_id=payload.tenant_id, user_id=payload.user.id
        ):
            return payload.user

        if payload.policy == SsoAutoProvisionPolicy.DISABLED:
            raise SsoProvisioningError(
                "SSO access is restricted to existing members.",
                reason="policy_disabled",
            )

        if not payload.email or not payload.email_verified:
            raise SsoProvisioningError(
                "Verified email is required for SSO provisioning.",
                reason="email_unverified",
            )

        if payload.policy == SsoAutoProvisionPolicy.INVITE_ONLY:
            return await self._accept_invite(payload=payload)

        if payload.policy == SsoAutoProvisionPolicy.DOMAIN_ALLOWLIST:
            return await self._provision_from_domain(payload=payload)

        raise SsoProvisioningError(
            "Unsupported SSO provisioning policy.",
            reason="policy_unsupported",
        )

    async def _accept_invite(self, *, payload: SsoProvisioningInput) -> UserRecord:
        try:
            acceptance = await self._invite_acceptance_service.accept_best_invite(
                tenant_id=payload.tenant_id,
                email=payload.email or "",
                existing_user=payload.user,
                display_name=payload.display_name,
                now=payload.now or datetime.now(UTC),
            )
        except TeamInviteRequiredError as exc:
            raise SsoProvisioningError(
                "An active invite is required for SSO.",
                reason="invite_required",
            ) from exc
        except TeamInviteInvalidError as exc:
            raise SsoProvisioningError(
                "Invite validation failed for SSO provisioning.",
                reason="invite_invalid",
            ) from exc

        log_event(
            "auth.sso.provisioned",
            result="success",
            policy="invite_only",
            tenant_id=str(payload.tenant_id),
            user_id=str(acceptance.user.id),
        )
        return acceptance.user

    async def _provision_from_domain(self, *, payload: SsoProvisioningInput) -> UserRecord:
        if not email_domain_allowed(payload.email or "", payload.allowed_domains):
            raise SsoProvisioningError(
                "Email domain is not allowed for SSO provisioning.",
                reason="domain_not_allowed",
            )

        result = await self._user_provisioning_service.provision_user(
            request=UserProvisioningRequest(
                tenant_id=payload.tenant_id,
                email=payload.email or "",
                default_role=payload.default_role,
                display_name=payload.display_name,
                email_verified=payload.email_verified,
                existing_user=payload.user,
                now=payload.now,
            )
        )

        if result.created or result.membership_added:
            log_event(
                "auth.sso.provisioned",
                result="success",
                policy="domain_allowlist",
                tenant_id=str(payload.tenant_id),
                user_id=str(result.user.id),
            )
        return result.user


__all__ = ["SsoProvisioner", "SsoProvisioningInput"]
