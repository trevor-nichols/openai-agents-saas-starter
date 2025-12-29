"""Tenant membership management service."""

from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from app.core.settings import Settings, get_settings
from app.domain.team import TeamMember, TeamMemberListResult, TenantMembershipRepository
from app.domain.team_errors import TeamMemberAlreadyExistsError, TeamMemberNotFoundError
from app.domain.tenant_roles import TenantRole, normalize_tenant_role
from app.domain.users import UserRepository
from app.infrastructure.persistence.auth.membership_repository import (
    get_tenant_membership_repository,
)
from app.infrastructure.persistence.auth.user_repository import get_user_repository
from app.services.users.errors import LastOwnerRemovalError

from .roles import ensure_owner_role_change_allowed, normalize_team_role


class TenantMembershipService:
    def __init__(
        self,
        membership_repository: TenantMembershipRepository,
        user_repository: UserRepository,
    ) -> None:
        self._membership_repository = membership_repository
        self._user_repository = user_repository

    async def list_members(
        self,
        *,
        tenant_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> TeamMemberListResult:
        return await self._membership_repository.list_members(
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
        )

    async def add_member(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        role: str,
        actor_role: TenantRole,
    ) -> TeamMember:
        normalized_role = normalize_team_role(role)
        ensure_owner_role_change_allowed(
            actor_role=actor_role,
            target_role=normalized_role,
        )
        if await self._membership_repository.membership_exists(
            tenant_id=tenant_id, user_id=user_id
        ):
            raise TeamMemberAlreadyExistsError(
                "User is already a member of this tenant."
            )
        user = await self._user_repository.get_user_by_id(user_id)
        if user is None:
            raise TeamMemberNotFoundError("User not found.")
        return await self._membership_repository.add_member(
            tenant_id=tenant_id,
            user_id=user_id,
            role=normalized_role.value,
        )

    async def add_member_by_email(
        self,
        *,
        tenant_id: UUID,
        email: str,
        role: str,
        actor_role: TenantRole,
    ) -> TeamMember:
        user = await self._user_repository.get_user_by_email(email)
        if user is None:
            raise TeamMemberNotFoundError("User not found.")
        return await self.add_member(
            tenant_id=tenant_id,
            user_id=user.id,
            role=role,
            actor_role=actor_role,
        )

    async def update_role(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        role: str,
        actor_role: TenantRole,
    ) -> TeamMember:
        normalized_role = normalize_team_role(role)
        current = await self._membership_repository.get_member(
            tenant_id=tenant_id, user_id=user_id
        )
        if current is None:
            raise TeamMemberNotFoundError("Member not found.")
        current_role = normalize_tenant_role(current.role)
        ensure_owner_role_change_allowed(
            actor_role=actor_role,
            current_role=current_role,
            target_role=normalized_role,
        )
        if current.role.lower() == "owner" and normalized_role is not TenantRole.OWNER:
            await self._ensure_not_last_owner(tenant_id)
        updated = await self._membership_repository.update_role(
            tenant_id=tenant_id,
            user_id=user_id,
            role=normalized_role.value,
        )
        if updated is None:
            raise TeamMemberNotFoundError("Member not found.")
        return updated

    async def remove_member(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        actor_role: TenantRole,
    ) -> None:
        current = await self._membership_repository.get_member(
            tenant_id=tenant_id, user_id=user_id
        )
        if current is None:
            raise TeamMemberNotFoundError("Member not found.")
        current_role = normalize_tenant_role(current.role)
        ensure_owner_role_change_allowed(
            actor_role=actor_role,
            current_role=current_role,
        )
        if current.role.lower() == "owner":
            await self._ensure_not_last_owner(tenant_id)
        removed = await self._membership_repository.remove_member(
            tenant_id=tenant_id,
            user_id=user_id,
        )
        if not removed:
            raise TeamMemberNotFoundError("Member not found.")

    async def _ensure_not_last_owner(self, tenant_id: UUID) -> None:
        count = await self._membership_repository.count_members_by_role(
            tenant_id=tenant_id, role="owner"
        )
        if count <= 1:
            raise LastOwnerRemovalError(
                "Cannot remove or demote the last owner of a tenant."
            )


def _normalize_role(role: str) -> TenantRole:
    return normalize_team_role(role)


def normalize_roles(roles: Iterable[str]) -> list[str]:
    return [_normalize_role(role).value for role in roles]


def build_tenant_membership_service(
    *,
    settings: Settings | None = None,
    membership_repository: TenantMembershipRepository | None = None,
    user_repository: UserRepository | None = None,
) -> TenantMembershipService:
    resolved_settings = settings or get_settings()
    resolved_membership_repo = (
        membership_repository
        or get_tenant_membership_repository(resolved_settings)
    )
    if resolved_membership_repo is None:
        raise RuntimeError("Tenant membership repository is not configured.")
    resolved_user_repo = user_repository or get_user_repository(resolved_settings)
    if resolved_user_repo is None:
        raise RuntimeError("User repository is not configured.")
    return TenantMembershipService(resolved_membership_repo, resolved_user_repo)


def get_tenant_membership_service() -> TenantMembershipService:
    from app.bootstrap.container import get_container

    container = get_container()
    if container.team_membership_service is None:
        container.team_membership_service = build_tenant_membership_service()
    return container.team_membership_service


__all__ = [
    "TenantMembershipService",
    "build_tenant_membership_service",
    "get_tenant_membership_service",
    "normalize_roles",
]
