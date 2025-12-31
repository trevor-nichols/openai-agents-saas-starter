"""Role normalization and policy checks for team management."""

from __future__ import annotations

from app.domain.team_errors import InvalidTeamRoleError, OwnerRoleAssignmentError
from app.domain.tenant_roles import TenantRole, normalize_tenant_role


def normalize_team_role(value: TenantRole | str) -> TenantRole:
    if isinstance(value, TenantRole):
        return value
    normalized = normalize_tenant_role(value)
    if normalized is None:
        raise InvalidTeamRoleError("Unsupported team role.")
    return normalized


def ensure_owner_role_change_allowed(
    *,
    actor_role: TenantRole,
    current_role: TenantRole | None = None,
    target_role: TenantRole | None = None,
) -> None:
    """Only owners can grant or revoke the owner role."""

    if actor_role is TenantRole.OWNER:
        return
    if current_role is TenantRole.OWNER or target_role is TenantRole.OWNER:
        raise OwnerRoleAssignmentError(
            "Only tenant owners can grant or revoke the owner role."
        )


__all__ = ["ensure_owner_role_change_allowed", "normalize_team_role"]
