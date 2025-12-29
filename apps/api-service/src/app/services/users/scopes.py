"""Role-to-scope policy."""

from __future__ import annotations

from collections.abc import Iterable

from app.domain.tenant_roles import TenantRole, max_tenant_role


def scopes_for_role(role: str | TenantRole) -> list[str]:
    normalized = (
        role.value if isinstance(role, TenantRole) else str(role).lower().strip()
    )
    if normalized in {"platform_operator", "platform-operator"}:
        return [
            "platform:operator",
            "auth:invites",
            "auth:signup_requests",
            "support:read",
            "activity:read",
        ]
    if normalized in {"admin", "owner"}:
        return [
            "conversations:read",
            "conversations:write",
            "conversations:delete",
            "workflows:delete",
            "tools:read",
            "billing:read",
            "billing:manage",
            "support:read",
            "activity:read",
        ]
    if normalized == "member":
        return [
            "conversations:read",
            "conversations:write",
            "tools:read",
        ]
    return [
        "conversations:read",
        "tools:read",
    ]


def role_for_scopes(scopes: Iterable[str]) -> TenantRole | None:
    """Resolve the least-privileged tenant role implied by a scope list."""

    resolved: TenantRole | None = None
    for scope in scopes:
        normalized = scope.lower().strip()
        if normalized in {
            "billing:manage",
            "workflows:delete",
            "conversations:delete",
            "support:read",
            "activity:read",
        }:
            resolved = max_tenant_role(resolved, TenantRole.ADMIN)
            continue
        if normalized == "billing:read":
            resolved = max_tenant_role(resolved, TenantRole.VIEWER)
            continue
        if normalized == "conversations:write":
            resolved = max_tenant_role(resolved, TenantRole.MEMBER)
            continue
        if normalized in {"conversations:read", "tools:read"}:
            resolved = max_tenant_role(resolved, TenantRole.VIEWER)
            continue
    return resolved


__all__ = ["role_for_scopes", "scopes_for_role"]
