"""Tenant membership resolution helpers."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from app.domain.users import TenantMembershipDTO

from .errors import MembershipNotFoundError, TenantContextRequiredError


def resolve_membership(
    memberships: Sequence[TenantMembershipDTO], tenant_id: UUID | None
) -> TenantMembershipDTO:
    if not memberships:
        raise MembershipNotFoundError("User is not assigned to any tenant.")
    if tenant_id:
        for membership in memberships:
            if membership.tenant_id == tenant_id:
                return membership
        raise MembershipNotFoundError("User is not a member of the requested tenant.")
    if len(memberships) > 1:
        raise TenantContextRequiredError("Tenant context required for multi-tenant users.")
    return memberships[0]


__all__ = ["resolve_membership"]
