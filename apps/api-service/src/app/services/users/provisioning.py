"""User provisioning helpers for onboarding flows."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app.core.security import PASSWORD_HASH_VERSION, get_password_hash
from app.core.settings import Settings, get_settings
from app.domain.team import TenantMembershipRepository
from app.domain.team_errors import TeamMemberAlreadyExistsError
from app.domain.tenant_roles import TenantRole
from app.domain.users import (
    UserCreatePayload,
    UserProfilePatch,
    UserRecord,
    UserRepository,
    UserRepositoryError,
    UserStatus,
)
from app.infrastructure.persistence.auth.membership_repository import (
    get_tenant_membership_repository,
)
from app.infrastructure.persistence.auth.user_repository import get_user_repository


@dataclass(slots=True)
class UserProvisioningRequest:
    tenant_id: UUID
    email: str
    default_role: TenantRole
    display_name: str | None
    email_verified: bool
    existing_user: UserRecord | None = None
    profile_update: UserProfilePatch | None = None
    profile_fields: set[str] | None = None
    now: datetime | None = None


@dataclass(slots=True)
class UserProvisioningResult:
    user: UserRecord
    created: bool
    membership_added: bool


class UserProvisioningError(RuntimeError):
    """Base error for user provisioning."""


class UserProvisioningConflictError(UserProvisioningError):
    """Raised when user provisioning cannot resolve a race or conflict."""


class UserProvisioningService:
    def __init__(
        self,
        *,
        user_repository: UserRepository,
        membership_repository: TenantMembershipRepository,
    ) -> None:
        self._user_repository = user_repository
        self._membership_repository = membership_repository

    async def provision_user(
        self,
        *,
        request: UserProvisioningRequest,
    ) -> UserProvisioningResult:
        now = request.now or datetime.now(UTC)
        user = request.existing_user
        created = False
        membership_added = False

        if user is None:
            password_seed = secrets.token_urlsafe(32)
            payload = UserCreatePayload(
                email=request.email,
                password_hash=get_password_hash(password_seed),
                password_pepper_version=PASSWORD_HASH_VERSION,
                status=UserStatus.ACTIVE,
                tenant_id=request.tenant_id,
                role=request.default_role,
                display_name=request.display_name,
            )
            try:
                user = await self._user_repository.create_user(payload)
                created = True
                membership_added = True
            except UserRepositoryError as exc:
                existing = await self._user_repository.get_user_by_email(request.email)
                if existing is None:
                    raise UserProvisioningError("Failed to provision user.") from exc
                user = existing
                if not await self._membership_repository.membership_exists(
                    tenant_id=request.tenant_id,
                    user_id=user.id,
                ):
                    try:
                        await self._membership_repository.add_member(
                            tenant_id=request.tenant_id,
                            user_id=user.id,
                            role=request.default_role,
                        )
                        membership_added = True
                    except TeamMemberAlreadyExistsError:
                        membership_added = False

        else:
            if not await self._membership_repository.membership_exists(
                tenant_id=request.tenant_id,
                user_id=user.id,
            ):
                try:
                    await self._membership_repository.add_member(
                        tenant_id=request.tenant_id,
                        user_id=user.id,
                        role=request.default_role,
                    )
                    membership_added = True
                except TeamMemberAlreadyExistsError:
                    membership_added = False

        if request.profile_update and request.profile_fields:
            await self._user_repository.upsert_user_profile(
                user.id,
                request.profile_update,
                provided_fields=request.profile_fields,
            )

        if request.email_verified and user.email_verified_at is None:
            await self._user_repository.mark_email_verified(user.id, timestamp=now)

        return UserProvisioningResult(
            user=user,
            created=created,
            membership_added=membership_added,
        )


def build_user_provisioning_service(
    *, settings: Settings | None = None
) -> UserProvisioningService:
    resolved_settings = settings or get_settings()
    user_repository = get_user_repository(resolved_settings)
    membership_repository = get_tenant_membership_repository(resolved_settings)
    if user_repository is None:
        raise RuntimeError("User repository is not configured.")
    if membership_repository is None:
        raise RuntimeError("Tenant membership repository is not configured.")
    return UserProvisioningService(
        user_repository=user_repository,
        membership_repository=membership_repository,
    )


__all__ = [
    "UserProvisioningConflictError",
    "UserProvisioningError",
    "UserProvisioningRequest",
    "UserProvisioningResult",
    "UserProvisioningService",
    "build_user_provisioning_service",
]
