"""Unit tests for team invite acceptance service."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from app.domain.team import TeamInvite, TeamInviteStatus
from app.domain.team_errors import TeamInviteUserExistsError
from app.domain.tenant_roles import TenantRole
from app.domain.users import UserRecord, UserStatus
from app.services.team.acceptance_service import (
    TeamInviteAcceptanceService,
    TeamInviteAcceptanceResult,
)


class FakeInviteRepo:
    def __init__(self, invites: list[TeamInvite]) -> None:
        self.invites = invites
        self.accepted: list[UUID] = []

    async def list_invites(
        self,
        *,
        tenant_id: UUID,
        status: TeamInviteStatus | None,
        email: str | None,
        limit: int,
        offset: int,
    ):
        return SimpleNamespace(invites=self.invites, total=len(self.invites))

    async def mark_accepted(
        self,
        invite_id: UUID,
        *,
        timestamp: datetime,
        accepted_by_user_id: UUID,
    ) -> TeamInvite | None:
        self.accepted.append(invite_id)
        return None


class FakeAcceptanceRepo:
    def __init__(self) -> None:
        self.accepted_existing: list[UUID] = []

    async def accept_for_new_user(self, *args, **kwargs):
        raise TeamInviteUserExistsError("Account already exists.")

    async def accept_for_existing_user(
        self,
        *,
        token_hash: str,
        user_id: UUID,
        now: datetime,
    ) -> TeamInvite:
        self.accepted_existing.append(user_id)
        return _build_invite(token_hash=token_hash)


class FakeUserRepo:
    def __init__(self, user: UserRecord) -> None:
        self.user = user

    async def get_user_by_id(self, user_id: UUID) -> UserRecord | None:
        return self.user if self.user.id == user_id else None

    async def get_user_by_email(self, email: str) -> UserRecord | None:
        return self.user if self.user.email == email else None


@pytest.mark.asyncio
async def test_accept_best_invite_falls_back_to_existing_user() -> None:
    invite = _build_invite()
    user = _build_user("owner@example.com")

    service = TeamInviteAcceptanceService(
        invite_repository=cast(Any, FakeInviteRepo([invite])),
        acceptance_repository=cast(Any, FakeAcceptanceRepo()),
        user_repository=cast(Any, FakeUserRepo(user)),
    )

    result = await service.accept_best_invite(
        tenant_id=invite.tenant_id,
        email=user.email,
        existing_user=None,
        display_name=None,
    )

    assert isinstance(result, TeamInviteAcceptanceResult)
    assert result.user.id == user.id
    assert result.created_user is False


def _build_invite(*, token_hash: str = "token") -> TeamInvite:
    now = datetime.now(UTC)
    return TeamInvite(
        id=uuid4(),
        tenant_id=uuid4(),
        token_hash=token_hash,
        token_hint="hint",
        invited_email="owner@example.com",
        role=TenantRole.MEMBER,
        status=TeamInviteStatus.ACTIVE,
        created_by_user_id=None,
        accepted_by_user_id=None,
        accepted_at=None,
        revoked_at=None,
        revoked_reason=None,
        expires_at=None,
        created_at=now,
        updated_at=now,
    )


def _build_user(email: str) -> UserRecord:
    now = datetime.now(UTC)
    return UserRecord(
        id=uuid4(),
        email=email,
        status=UserStatus.ACTIVE,
        password_hash="hash",
        password_pepper_version="v2",
        created_at=now,
        updated_at=now,
        display_name=None,
        given_name=None,
        family_name=None,
        avatar_url=None,
        timezone=None,
        locale=None,
        memberships=[],
        email_verified_at=None,
        platform_role=None,
    )

