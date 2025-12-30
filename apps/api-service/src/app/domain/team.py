"""Domain models and repository protocols for tenant team management."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol
from uuid import UUID

from app.domain.tenant_roles import TenantRole
from app.domain.users import UserStatus


class TeamInviteStatus(str, Enum):
    """Lifecycle states for tenant member invites."""

    ACTIVE = "active"
    ACCEPTED = "accepted"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass(slots=True)
class TeamMember:
    user_id: UUID
    tenant_id: UUID
    email: str
    display_name: str | None
    role: TenantRole
    status: UserStatus
    email_verified: bool
    joined_at: datetime


@dataclass(slots=True)
class TeamMemberListResult:
    members: list[TeamMember]
    total: int


class TenantMembershipRepository(Protocol):
    async def list_members(
        self,
        *,
        tenant_id: UUID,
        limit: int,
        offset: int,
    ) -> TeamMemberListResult: ...

    async def get_member(self, *, tenant_id: UUID, user_id: UUID) -> TeamMember | None: ...

    async def add_member(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        role: TenantRole,
    ) -> TeamMember: ...

    async def update_role(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        role: TenantRole,
    ) -> TeamMember | None: ...

    async def remove_member(self, *, tenant_id: UUID, user_id: UUID) -> bool: ...

    async def membership_exists(self, *, tenant_id: UUID, user_id: UUID) -> bool: ...

    async def count_members_by_role(
        self, *, tenant_id: UUID, role: TenantRole
    ) -> int: ...


@dataclass(slots=True)
class TeamInvite:
    id: UUID
    tenant_id: UUID
    token_hash: str
    token_hint: str
    invited_email: str
    role: TenantRole
    status: TeamInviteStatus
    created_by_user_id: UUID | None
    accepted_by_user_id: UUID | None
    accepted_at: datetime | None
    revoked_at: datetime | None
    revoked_reason: str | None
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class TeamInviteCreate:
    tenant_id: UUID
    token_hash: str
    token_hint: str
    invited_email: str
    role: TenantRole
    created_by_user_id: UUID | None
    expires_at: datetime | None


@dataclass(slots=True)
class TeamInviteListResult:
    invites: list[TeamInvite]
    total: int


@dataclass(slots=True)
class TeamInviteAcceptResult:
    invite_id: UUID
    user_id: UUID
    tenant_id: UUID
    email: str


class TeamInviteRepository(Protocol):
    async def create(self, payload: TeamInviteCreate) -> TeamInvite: ...

    async def get(self, invite_id: UUID) -> TeamInvite | None: ...

    async def find_by_token_hash(self, token_hash: str) -> TeamInvite | None: ...

    async def list_invites(
        self,
        *,
        tenant_id: UUID,
        status: TeamInviteStatus | None,
        email: str | None,
        limit: int,
        offset: int,
    ) -> TeamInviteListResult: ...

    async def mark_revoked(
        self,
        invite_id: UUID,
        *,
        tenant_id: UUID,
        timestamp: datetime,
        reason: str | None,
    ) -> TeamInvite | None: ...

    async def mark_accepted(
        self,
        invite_id: UUID,
        *,
        timestamp: datetime,
        accepted_by_user_id: UUID,
    ) -> TeamInvite | None: ...

    async def mark_expired(self, invite_id: UUID, *, timestamp: datetime) -> TeamInvite | None: ...


class TeamInviteAcceptanceRepository(Protocol):
    async def accept_for_new_user(
        self,
        *,
        token_hash: str,
        password_hash: str,
        password_pepper_version: str,
        display_name: str | None,
        now: datetime,
    ) -> TeamInviteAcceptResult: ...

    async def accept_for_existing_user(
        self,
        *,
        token_hash: str,
        user_id: UUID,
        now: datetime,
    ) -> TeamInvite: ...


__all__ = [
    "TeamInviteAcceptResult",
    "TeamInvite",
    "TeamInviteCreate",
    "TeamInviteListResult",
    "TeamInviteAcceptanceRepository",
    "TeamInviteRepository",
    "TeamInviteStatus",
    "TeamMember",
    "TeamMemberListResult",
    "TenantMembershipRepository",
]
