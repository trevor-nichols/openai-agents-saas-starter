"""Unit tests for tenant invite service."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.team import (
    TeamInvite,
    TeamInviteAcceptResult,
    TeamInviteAcceptanceRepository,
    TeamInviteCreate,
    TeamInviteRepository,
    TeamInviteStatus,
    TenantMembershipRepository,
)
from app.domain.tenant_accounts import TenantAccountRepository
from app.domain.team_policy import TEAM_INVITE_POLICY
from app.domain.tenant_roles import TenantRole
from app.domain.users import (
    TenantMembershipDTO,
    UserCreatePayload,
    UserRecord,
    UserRepository,
    UserStatus,
)
from app.infrastructure.persistence.auth.models.membership import TenantUserMembership
from app.infrastructure.persistence.auth.models.team_invites import TenantMemberInvite
from app.infrastructure.persistence.auth.models.user import (
    UserAccount,
    PasswordHistory,
    UserStatus as DBUserStatus,
)
from app.infrastructure.persistence.auth.team_invite_acceptance_repository import (
    PostgresTeamInviteAcceptanceRepository,
)
from app.infrastructure.persistence.auth.team_invite_repository import (
    PostgresTeamInviteRepository,
)
from app.infrastructure.persistence.tenants.models import TenantAccount
from app.domain.team_errors import (
    OwnerRoleAssignmentError,
    TeamInviteEmailMismatchError,
    TeamInviteExpiredError,
    TeamInviteNotFoundError,
    TeamInviteRevokedError,
    TeamInviteValidationError,
    TeamMemberAlreadyExistsError,
)
from app.services.team.invite_service import TeamInviteService
from app.bootstrap.container import get_container


class FakeInviteRepository:
    def __init__(self, invite: TeamInvite | None = None) -> None:
        self.invite = invite
        self.expired: list[UUID] = []
        self.accepted: list[UUID] = []
        self.created: list[TeamInvite] = []

    async def create(self, payload: TeamInviteCreate) -> TeamInvite:
        invite = TeamInvite(
            id=uuid4(),
            tenant_id=payload.tenant_id,
            token_hash=payload.token_hash,
            token_hint=payload.token_hint,
            invited_email=payload.invited_email,
            role=payload.role,
            status=TeamInviteStatus.ACTIVE,
            created_by_user_id=payload.created_by_user_id,
            accepted_by_user_id=None,
            accepted_at=None,
            revoked_at=None,
            revoked_reason=None,
            expires_at=payload.expires_at,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.created.append(invite)
        return invite

    async def get(self, invite_id: UUID) -> TeamInvite | None:
        if self.invite and self.invite.id == invite_id:
            return self.invite
        return None

    async def find_by_token_hash(self, token_hash: str) -> TeamInvite | None:
        return self.invite

    async def list_invites(
        self,
        *,
        tenant_id: UUID,
        status: TeamInviteStatus | None,
        email: str | None,
        limit: int,
        offset: int,
    ):
        raise NotImplementedError

    async def mark_revoked(
        self,
        invite_id: UUID,
        *,
        tenant_id: UUID,
        timestamp: datetime,
        reason: str | None,
    ) -> TeamInvite | None:
        if self.invite is None:
            return None
        if self.invite.id != invite_id or self.invite.tenant_id != tenant_id:
            return None
        if self.invite.status is not TeamInviteStatus.ACTIVE:
            return None
        self.invite.status = TeamInviteStatus.REVOKED
        self.invite.revoked_at = timestamp
        self.invite.revoked_reason = reason
        return self.invite

    async def mark_accepted(
        self,
        invite_id: UUID,
        *,
        timestamp: datetime,
        accepted_by_user_id: UUID,
    ) -> TeamInvite | None:
        if self.invite is None:
            return None
        self.accepted.append(invite_id)
        self.invite.status = TeamInviteStatus.ACCEPTED
        self.invite.accepted_by_user_id = accepted_by_user_id
        self.invite.accepted_at = timestamp
        return self.invite

    async def mark_expired(self, invite_id: UUID, *, timestamp: datetime) -> TeamInvite | None:
        if self.invite is None:
            return None
        self.expired.append(invite_id)
        self.invite.status = TeamInviteStatus.EXPIRED
        self.invite.revoked_at = timestamp
        self.invite.revoked_reason = "expired"
        return self.invite


class FakeMembershipRepository:
    def __init__(self, *, exists: bool = False) -> None:
        self.exists = exists
        self.added: list[tuple[UUID, UUID, TenantRole]] = []

    async def membership_exists(self, *, tenant_id: UUID, user_id: UUID) -> bool:
        return self.exists

    async def add_member(self, *, tenant_id: UUID, user_id: UUID, role: TenantRole) -> None:
        self.added.append((tenant_id, user_id, role))


class FakeUserRepository:
    def __init__(self, user: UserRecord | None) -> None:
        self._user = user
        self.created: list[UserCreatePayload] = []
        self.verified: list[UUID] = []

    async def get_user_by_email(self, email: str) -> UserRecord | None:
        if self._user and self._user.email == email:
            return self._user
        return None

    async def get_user_by_id(self, user_id: UUID) -> UserRecord | None:
        if self._user and self._user.id == user_id:
            return self._user
        return None

    async def create_user(self, payload: UserCreatePayload) -> UserRecord:
        self.created.append(payload)
        record = build_user(payload.email)
        self._user = record
        return record

    async def mark_email_verified(self, user_id: UUID, *, timestamp: datetime) -> None:
        self.verified.append(user_id)


class FakeTenantRepository:
    def __init__(self, name: str = "Acme") -> None:
        self._name = name

    async def get_name(self, tenant_id: UUID) -> str | None:
        return self._name


class FakeAcceptanceRepository:
    async def accept_for_new_user(
        self,
        *,
        token_hash: str,
        password_hash: str,
        password_pepper_version: str,
        display_name: str | None,
        now: datetime,
    ) -> TeamInviteAcceptResult:
        raise AssertionError("accept_for_new_user should not be called in this test.")

    async def accept_for_existing_user(
        self,
        *,
        token_hash: str,
        user_id: UUID,
        now: datetime,
    ) -> TeamInvite:
        raise AssertionError("accept_for_existing_user should not be called in this test.")


@pytest.fixture
def session_factory() -> async_sessionmaker[AsyncSession]:
    container = get_container()
    assert container.session_factory is not None
    return container.session_factory


@pytest.mark.asyncio
async def test_issue_invite_blocks_existing_member(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id = uuid4()
    user = build_user("member@example.com")
    membership_repo = FakeMembershipRepository(exists=True)
    invite_repo = PostgresTeamInviteRepository(session_factory)
    user_repo = FakeUserRepository(user)

    service = TeamInviteService(
        invite_repository=cast(TeamInviteRepository, invite_repo),
        acceptance_repository=cast(TeamInviteAcceptanceRepository, FakeAcceptanceRepository()),
        user_repository=cast(UserRepository, user_repo),
        membership_repository=cast(TenantMembershipRepository, membership_repo),
        tenant_repository=cast(TenantAccountRepository, FakeTenantRepository()),
        notifier=None,
    )

    with pytest.raises(TeamMemberAlreadyExistsError):
        await service.issue_invite(
            tenant_id=tenant_id,
            invited_email=user.email,
            role=TenantRole.MEMBER,
            created_by_user_id=None,
            actor_role=TenantRole.ADMIN,
        )


@pytest.mark.asyncio
async def test_issue_invite_rejects_expiry_over_policy_limit() -> None:
    tenant_id = uuid4()
    invite_repo = FakeInviteRepository()
    membership_repo = FakeMembershipRepository(exists=False)
    user_repo = FakeUserRepository(None)

    service = TeamInviteService(
        invite_repository=cast(TeamInviteRepository, invite_repo),
        acceptance_repository=cast(TeamInviteAcceptanceRepository, FakeAcceptanceRepository()),
        user_repository=cast(UserRepository, user_repo),
        membership_repository=cast(TenantMembershipRepository, membership_repo),
        tenant_repository=cast(TenantAccountRepository, FakeTenantRepository()),
        notifier=None,
    )

    with pytest.raises(TeamInviteValidationError):
        await service.issue_invite(
            tenant_id=tenant_id,
            invited_email="invitee@example.com",
            role=TenantRole.MEMBER,
            created_by_user_id=None,
            actor_role=TenantRole.ADMIN,
            expires_in_hours=TEAM_INVITE_POLICY.max_expires_hours + 1,
        )


@pytest.mark.asyncio
async def test_accept_invite_marks_expired(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    now = datetime.now(UTC)
    tenant_id = await seed_tenant(session_factory)
    token = f"invite-{uuid4().hex}"
    invite_email = f"invitee-{uuid4().hex[:8]}@example.com"
    invite_id = await seed_invite(
        session_factory,
        tenant_id=tenant_id,
        token=token,
        invited_email=invite_email,
        expires_at=now - timedelta(hours=1),
    )
    invite_repo = PostgresTeamInviteRepository(session_factory)
    membership_repo = FakeMembershipRepository(exists=False)
    user_repo = FakeUserRepository(None)

    service = TeamInviteService(
        invite_repository=cast(TeamInviteRepository, invite_repo),
        acceptance_repository=PostgresTeamInviteAcceptanceRepository(session_factory),
        user_repository=cast(UserRepository, user_repo),
        membership_repository=cast(TenantMembershipRepository, membership_repo),
        tenant_repository=cast(TenantAccountRepository, FakeTenantRepository()),
        notifier=None,
    )

    with pytest.raises(TeamInviteExpiredError):
        await service.accept_invite_for_new_user(
            token=token,
            password="ValidPassword!!123",
            display_name=None,
        )

    async with session_factory() as session:
        record = await session.get(TenantMemberInvite, invite_id)
        assert record is not None
        assert record.status == TeamInviteStatus.EXPIRED


@pytest.mark.asyncio
async def test_accept_invite_creates_user_membership_and_history(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id = await seed_tenant(session_factory)
    token = f"invite-{uuid4().hex}"
    invite_email = f"invitee-{uuid4().hex[:8]}@example.com"
    invite_id = await seed_invite(
        session_factory,
        tenant_id=tenant_id,
        token=token,
        invited_email=invite_email,
    )
    invite_repo = PostgresTeamInviteRepository(session_factory)
    membership_repo = FakeMembershipRepository(exists=False)
    user_repo = FakeUserRepository(None)

    service = TeamInviteService(
        invite_repository=cast(TeamInviteRepository, invite_repo),
        acceptance_repository=PostgresTeamInviteAcceptanceRepository(session_factory),
        user_repository=cast(UserRepository, user_repo),
        membership_repository=cast(TenantMembershipRepository, membership_repo),
        tenant_repository=cast(TenantAccountRepository, FakeTenantRepository()),
        notifier=None,
    )

    result = await service.accept_invite_for_new_user(
        token=token,
        password="ValidPassword!!123",
        display_name="Invitee",
    )

    async with session_factory() as session:
        user = await session.get(UserAccount, result.user_id)
        assert user is not None
        assert user.email_verified_at is not None

        membership = await session.scalar(
            select(TenantUserMembership).where(
                TenantUserMembership.tenant_id == tenant_id,
                TenantUserMembership.user_id == result.user_id,
            )
        )
        assert membership is not None

        history = await session.scalar(
            select(PasswordHistory).where(PasswordHistory.user_id == result.user_id)
        )
        assert history is not None

        invite = await session.get(TenantMemberInvite, invite_id)
        assert invite is not None
        assert invite.status == TeamInviteStatus.ACCEPTED


@pytest.mark.asyncio
async def test_accept_invite_existing_user_requires_email_match(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id = await seed_tenant(session_factory)
    token = f"invite-{uuid4().hex}"
    invite_email = f"invitee-{uuid4().hex[:8]}@example.com"
    other_email = f"other-{uuid4().hex[:8]}@example.com"
    await seed_invite(
        session_factory,
        tenant_id=tenant_id,
        token=token,
        invited_email=invite_email,
    )
    user_id = await seed_user(session_factory, email=other_email)
    invite_repo = PostgresTeamInviteRepository(session_factory)
    membership_repo = FakeMembershipRepository(exists=False)
    user_repo = FakeUserRepository(None)

    service = TeamInviteService(
        invite_repository=cast(TeamInviteRepository, invite_repo),
        acceptance_repository=PostgresTeamInviteAcceptanceRepository(session_factory),
        user_repository=cast(UserRepository, user_repo),
        membership_repository=cast(TenantMembershipRepository, membership_repo),
        tenant_repository=cast(TenantAccountRepository, FakeTenantRepository()),
        notifier=None,
    )

    with pytest.raises(TeamInviteEmailMismatchError):
        await service.accept_invite_for_existing_user(
            token=token,
            user_id=user_id,
        )


@pytest.mark.asyncio
async def test_accept_invite_existing_user_verifies_email(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id = await seed_tenant(session_factory)
    token = f"invite-{uuid4().hex}"
    invite_email = f"invitee-{uuid4().hex[:8]}@example.com"
    await seed_invite(
        session_factory,
        tenant_id=tenant_id,
        token=token,
        invited_email=invite_email,
    )
    user_id = await seed_user(session_factory, email=invite_email)
    invite_repo = PostgresTeamInviteRepository(session_factory)
    membership_repo = FakeMembershipRepository(exists=False)
    user_repo = FakeUserRepository(None)

    service = TeamInviteService(
        invite_repository=cast(TeamInviteRepository, invite_repo),
        acceptance_repository=PostgresTeamInviteAcceptanceRepository(session_factory),
        user_repository=cast(UserRepository, user_repo),
        membership_repository=cast(TenantMembershipRepository, membership_repo),
        tenant_repository=cast(TenantAccountRepository, FakeTenantRepository()),
        notifier=None,
    )

    await service.accept_invite_for_existing_user(
        token=token,
        user_id=user_id,
    )

    async with session_factory() as session:
        membership = await session.scalar(
            select(TenantUserMembership).where(
                TenantUserMembership.tenant_id == tenant_id,
                TenantUserMembership.user_id == user_id,
            )
        )
        assert membership is not None
        user = await session.get(UserAccount, user_id)
        assert user is not None
        assert user.email_verified_at is not None


@pytest.mark.asyncio
async def test_revoke_invite_blocks_non_active(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    invite = TeamInvite(
        id=uuid4(),
        tenant_id=uuid4(),
        token_hash="hash",
        token_hint="hint",
        invited_email="invitee@example.com",
        role=TenantRole.MEMBER,
        status=TeamInviteStatus.ACCEPTED,
        created_by_user_id=None,
        accepted_by_user_id=uuid4(),
        accepted_at=datetime.now(UTC),
        revoked_at=None,
        revoked_reason=None,
        expires_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    service = TeamInviteService(
        invite_repository=cast(TeamInviteRepository, FakeInviteRepository(invite)),
        acceptance_repository=cast(TeamInviteAcceptanceRepository, FakeAcceptanceRepository()),
        user_repository=cast(UserRepository, FakeUserRepository(None)),
        membership_repository=cast(TenantMembershipRepository, FakeMembershipRepository()),
        tenant_repository=cast(TenantAccountRepository, FakeTenantRepository()),
        notifier=None,
    )

    with pytest.raises(TeamInviteRevokedError):
        await service.revoke_invite(invite.id, tenant_id=invite.tenant_id)


@pytest.mark.asyncio
async def test_revoke_invite_blocks_already_revoked(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    invite = TeamInvite(
        id=uuid4(),
        tenant_id=uuid4(),
        token_hash="hash",
        token_hint="hint",
        invited_email="invitee@example.com",
        role=TenantRole.MEMBER,
        status=TeamInviteStatus.REVOKED,
        created_by_user_id=None,
        accepted_by_user_id=None,
        accepted_at=None,
        revoked_at=datetime.now(UTC),
        revoked_reason="manual",
        expires_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    service = TeamInviteService(
        invite_repository=cast(TeamInviteRepository, FakeInviteRepository(invite)),
        acceptance_repository=cast(TeamInviteAcceptanceRepository, FakeAcceptanceRepository()),
        user_repository=cast(UserRepository, FakeUserRepository(None)),
        membership_repository=cast(TenantMembershipRepository, FakeMembershipRepository()),
        tenant_repository=cast(TenantAccountRepository, FakeTenantRepository()),
        notifier=None,
    )

    with pytest.raises(TeamInviteRevokedError):
        await service.revoke_invite(invite.id, tenant_id=invite.tenant_id)


@pytest.mark.asyncio
async def test_issue_invite_owner_requires_owner(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id = uuid4()
    invite_repo = FakeInviteRepository()
    membership_repo = FakeMembershipRepository(exists=False)
    user_repo = FakeUserRepository(None)

    service = TeamInviteService(
        invite_repository=cast(TeamInviteRepository, invite_repo),
        acceptance_repository=cast(TeamInviteAcceptanceRepository, FakeAcceptanceRepository()),
        user_repository=cast(UserRepository, user_repo),
        membership_repository=cast(TenantMembershipRepository, membership_repo),
        tenant_repository=cast(TenantAccountRepository, FakeTenantRepository()),
        notifier=None,
    )

    with pytest.raises(OwnerRoleAssignmentError):
        await service.issue_invite(
            tenant_id=tenant_id,
            invited_email="owner@example.com",
            role=TenantRole.OWNER,
            created_by_user_id=None,
            actor_role=TenantRole.ADMIN,
        )


@pytest.mark.asyncio
async def test_revoke_invite_blocks_tenant_mismatch(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    invite = TeamInvite(
        id=uuid4(),
        tenant_id=uuid4(),
        token_hash="hash",
        token_hint="hint",
        invited_email="invitee@example.com",
        role=TenantRole.MEMBER,
        status=TeamInviteStatus.ACTIVE,
        created_by_user_id=None,
        accepted_by_user_id=None,
        accepted_at=None,
        revoked_at=None,
        revoked_reason=None,
        expires_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    service = TeamInviteService(
        invite_repository=cast(TeamInviteRepository, FakeInviteRepository(invite)),
        acceptance_repository=cast(TeamInviteAcceptanceRepository, FakeAcceptanceRepository()),
        user_repository=cast(UserRepository, FakeUserRepository(None)),
        membership_repository=cast(TenantMembershipRepository, FakeMembershipRepository()),
        tenant_repository=cast(TenantAccountRepository, FakeTenantRepository()),
        notifier=None,
    )

    with pytest.raises(TeamInviteNotFoundError):
        await service.revoke_invite(invite.id, tenant_id=uuid4())


def build_user(email: str) -> UserRecord:
    return UserRecord(
        id=uuid4(),
        email=email,
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
                tenant_id=uuid4(),
                role=TenantRole.MEMBER,
                created_at=datetime.now(UTC),
            )
        ],
        email_verified_at=datetime.now(UTC),
        platform_role=None,
    )


async def seed_tenant(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    name: str = "Acme",
) -> UUID:
    tenant_id = uuid4()
    async with session_factory() as session:
        async with session.begin():
            session.add(
                TenantAccount(
                    id=tenant_id,
                    slug=f"tenant-{tenant_id.hex[:8]}",
                    name=name,
                )
            )
    return tenant_id


async def seed_user(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    email: str,
) -> UUID:
    user_id = uuid4()
    now = datetime.now(UTC)
    async with session_factory() as session:
        async with session.begin():
            session.add(
                UserAccount(
                    id=user_id,
                    email=email,
                    password_hash="hash",
                    password_pepper_version="v2",
                    status=DBUserStatus.ACTIVE,
                    email_verified_at=None,
                    created_at=now,
                    updated_at=now,
                )
            )
    return user_id


async def seed_invite(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    tenant_id: UUID,
    token: str,
    invited_email: str,
    expires_at: datetime | None = None,
) -> UUID:
    now = datetime.now(UTC)
    digest = hashlib.sha256(token.strip().encode("utf-8")).hexdigest()
    invite_id = uuid4()
    async with session_factory() as session:
        async with session.begin():
            session.add(
                TenantMemberInvite(
                    id=invite_id,
                    tenant_id=tenant_id,
                    token_hash=digest,
                    token_hint=token[:8],
                    invited_email=invited_email,
                    role=TenantRole.MEMBER,
                    status=TeamInviteStatus.ACTIVE,
                    created_by_user_id=None,
                    accepted_by_user_id=None,
                    accepted_at=None,
                    revoked_at=None,
                    revoked_reason=None,
                    expires_at=expires_at,
                    created_at=now,
                    updated_at=now,
                )
            )
    return invite_id
