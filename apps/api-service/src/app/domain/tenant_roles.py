"""Tenant role taxonomy and comparison helpers."""

from __future__ import annotations

from enum import Enum
from typing import Any


class TenantRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


ROLE_PRIORITY: dict[TenantRole, int] = {
    TenantRole.VIEWER: 1,
    TenantRole.MEMBER: 2,
    TenantRole.ADMIN: 3,
    TenantRole.OWNER: 4,
}


def normalize_tenant_role(value: Any) -> TenantRole | None:
    if value is None:
        return None
    try:
        return TenantRole(str(value).strip().lower())
    except ValueError:
        return None


def max_tenant_role(
    current: TenantRole | None, candidate: TenantRole | None
) -> TenantRole | None:
    if candidate is None:
        return current
    if current is None:
        return candidate
    if ROLE_PRIORITY[candidate] > ROLE_PRIORITY[current]:
        return candidate
    return current


__all__ = ["ROLE_PRIORITY", "TenantRole", "max_tenant_role", "normalize_tenant_role"]
