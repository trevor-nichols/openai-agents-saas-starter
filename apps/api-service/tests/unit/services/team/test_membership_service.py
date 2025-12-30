"""Unit tests for tenant membership service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

import pytest

from app.domain.team import TeamMember, TeamMemberListResult, TenantMembershipRepository
from app.domain.tenant_roles import TenantRole
from app.domain.users import TenantMembershipDTO, UserRecord, UserRepository, UserStatus
from app.domain.team_errors import (
    OwnerRoleAssignmentError,
    TeamMemberAlreadyExistsError,
    TeamMemberNotFoundError,
)
from app.services.team.membership_service import TenantMembershipService
from app.services.users.errors import LastOwnerRemovalError


class FakeMembershipRepository:
    def __init__(
        self,
        *,
        member: TeamMember | None = None,
        exists: bool = False,
        owner_count: int = 1,
    ) -> None:
        self._member = member
        self._exists = exists
        self._owner_count = owner_count
        self.add_calls: list[tuple[UUID, UUID, TenantRole]] = []
        self.update_calls: list[tuple[UUID, UUID, TenantRole]] = []
        self.remove_calls: list[tuple[UUID, UUID]] = []

    async def list_members(
        self,
        *,
        tenant_id: UUID,
        limit: int,
        offset: int,
    ) -> TeamMemberListResult:
        members = [self._member] if self._member else []
        return TeamMemberListResult(
            members=members,
            total=len(members),
            owner_count=self._owner_count,
        )

    async def get_member(self, *, tenant_id: UUID, user_id: UUID) -> TeamMember | None:
        return self._member

    async def add_member(
        self, *, tenant_id: UUID, user_id: UUID, role: TenantRole
    ) -> TeamMember:
        self.add_calls.append((tenant_id, user_id, role))
        if self._member is None:
            self._member = make_member(user_id=user_id, tenant_id=tenant_id, role=role)
        return self._member

    async def update_role(
        self, *, tenant_id: UUID, user_id: UUID, role: TenantRole
    ) -> TeamMember | None:
        self.update_calls.append((tenant_id, user_id, role))
        if self._member is None:
            return None
        self._member.role = role
        return self._member

    async def remove_member(self, *, tenant_id: UUID, user_id: UUID) -> bool:
        self.remove_calls.append((tenant_id, user_id))
        return True

    async def membership_exists(self, *, tenant_id: UUID, user_id: UUID) -> bool:
        return self._exists

    async def count_members_by_role(self, *, tenant_id: UUID, role: TenantRole) -> int:
        return self._owner_count


class FakeUserRepository:
    def __init__(self, user: UserRecord | None) -> None:
        self._user = user

    async def get_user_by_id(self, user_id: UUID) -> UserRecord | None:
        if self._user and self._user.id == user_id:
            return self._user
        return None

    async def get_user_by_email(self, email: str) -> UserRecord | None:
        if self._user and self._user.email == email:
            return self._user
        return None


@pytest.fixture
def member() -> TeamMember:
    return make_member()


@pytest.fixture
def user_record(member: TeamMember) -> UserRecord:
    return UserRecord(
        id=member.user_id,
        email=member.email,
        status=UserStatus.ACTIVE,
        password_hash="hash",
        password_pepper_version="v2",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        display_name=None,
        given_name=None,
        family_name=None,
        avatar_url=None,
        timezone=None,
        locale=None,
        memberships=[
            TenantMembershipDTO(
                tenant_id=member.tenant_id,
                role=member.role,
                created_at=member.joined_at,
            )
        ],
        email_verified_at=datetime.now(UTC),
        platform_role=None,
    )


@pytest.mark.asyncio
async def test_add_member_rejects_existing_member(user_record: UserRecord) -> None:
    membership_repo = FakeMembershipRepository(exists=True)
    service = TenantMembershipService(
        cast(TenantMembershipRepository, membership_repo),
        cast(UserRepository, FakeUserRepository(user_record)),
    )

    with pytest.raises(TeamMemberAlreadyExistsError):
        await service.add_member(
            tenant_id=uuid4(),
            user_id=user_record.id,
            role=TenantRole.MEMBER,
            actor_role=TenantRole.ADMIN,
        )


@pytest.mark.asyncio
async def test_add_member_missing_user() -> None:
    membership_repo = FakeMembershipRepository(exists=False)
    service = TenantMembershipService(
        cast(TenantMembershipRepository, membership_repo),
        cast(UserRepository, FakeUserRepository(None)),
    )

    with pytest.raises(TeamMemberNotFoundError):
        await service.add_member(
            tenant_id=uuid4(),
            user_id=uuid4(),
            role=TenantRole.MEMBER,
            actor_role=TenantRole.ADMIN,
        )


@pytest.mark.asyncio
async def test_update_role_blocks_last_owner(member: TeamMember, user_record: UserRecord) -> None:
    member.role = TenantRole.OWNER
    membership_repo = FakeMembershipRepository(member=member, owner_count=1)
    service = TenantMembershipService(
        cast(TenantMembershipRepository, membership_repo),
        cast(UserRepository, FakeUserRepository(user_record)),
    )

    with pytest.raises(LastOwnerRemovalError):
        await service.update_role(
            tenant_id=member.tenant_id,
            user_id=member.user_id,
            role=TenantRole.MEMBER,
            actor_role=TenantRole.OWNER,
        )


@pytest.mark.asyncio
async def test_remove_member_blocks_last_owner(member: TeamMember, user_record: UserRecord) -> None:
    member.role = TenantRole.OWNER
    membership_repo = FakeMembershipRepository(member=member, owner_count=1)
    service = TenantMembershipService(
        cast(TenantMembershipRepository, membership_repo),
        cast(UserRepository, FakeUserRepository(user_record)),
    )

    with pytest.raises(LastOwnerRemovalError):
        await service.remove_member(
            tenant_id=member.tenant_id,
            user_id=member.user_id,
            actor_role=TenantRole.OWNER,
        )


@pytest.mark.asyncio
async def test_admin_cannot_assign_owner_role(user_record: UserRecord) -> None:
    membership_repo = FakeMembershipRepository(exists=False)
    service = TenantMembershipService(
        cast(TenantMembershipRepository, membership_repo),
        cast(UserRepository, FakeUserRepository(user_record)),
    )

    with pytest.raises(OwnerRoleAssignmentError):
        await service.add_member(
            tenant_id=uuid4(),
            user_id=user_record.id,
            role=TenantRole.OWNER,
            actor_role=TenantRole.ADMIN,
        )


@pytest.mark.asyncio
async def test_admin_cannot_demote_owner(member: TeamMember, user_record: UserRecord) -> None:
    member.role = TenantRole.OWNER
    membership_repo = FakeMembershipRepository(member=member, owner_count=2)
    service = TenantMembershipService(
        cast(TenantMembershipRepository, membership_repo),
        cast(UserRepository, FakeUserRepository(user_record)),
    )

    with pytest.raises(OwnerRoleAssignmentError):
        await service.update_role(
            tenant_id=member.tenant_id,
            user_id=member.user_id,
            role=TenantRole.ADMIN,
            actor_role=TenantRole.ADMIN,
        )


@pytest.mark.asyncio
async def test_admin_cannot_remove_owner(member: TeamMember, user_record: UserRecord) -> None:
    member.role = TenantRole.OWNER
    membership_repo = FakeMembershipRepository(member=member, owner_count=2)
    service = TenantMembershipService(
        cast(TenantMembershipRepository, membership_repo),
        cast(UserRepository, FakeUserRepository(user_record)),
    )

    with pytest.raises(OwnerRoleAssignmentError):
        await service.remove_member(
            tenant_id=member.tenant_id,
            user_id=member.user_id,
            actor_role=TenantRole.ADMIN,
        )


def make_member(
    *,
    user_id: UUID | None = None,
    tenant_id: UUID | None = None,
    role: TenantRole = TenantRole.MEMBER,
) -> TeamMember:
    return TeamMember(
        user_id=user_id or uuid4(),
        tenant_id=tenant_id or uuid4(),
        email="member@example.com",
        display_name="Member",
        role=role,
        status=UserStatus.ACTIVE,
        email_verified=True,
        joined_at=datetime.now(UTC),
    )
