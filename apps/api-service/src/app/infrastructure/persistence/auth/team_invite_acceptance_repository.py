"""Atomic acceptance workflows for tenant member invites."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import Settings, get_settings
from app.domain.team import (
    TeamInvite,
    TeamInviteAcceptanceRepository,
    TeamInviteAcceptResult,
    TeamInviteStatus,
)
from app.domain.team_errors import (
    TeamInviteEmailMismatchError,
    TeamInviteExpiredError,
    TeamInviteNotFoundError,
    TeamInviteRevokedError,
    TeamInviteUserExistsError,
    TeamInviteValidationError,
    TeamMemberAlreadyExistsError,
)
from app.infrastructure.db import get_async_sessionmaker
from app.infrastructure.persistence.auth.models.membership import TenantUserMembership
from app.infrastructure.persistence.auth.models.team_invites import TenantMemberInvite
from app.infrastructure.persistence.auth.models.user import (
    PasswordHistory,
    UserAccount,
    UserProfile,
)
from app.infrastructure.persistence.auth.models.user import (
    UserStatus as DBUserStatus,
)


class PostgresTeamInviteAcceptanceRepository(TeamInviteAcceptanceRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def accept_for_new_user(
        self,
        *,
        token_hash: str,
        password_hash: str,
        password_pepper_version: str,
        display_name: str | None,
        now: datetime,
    ) -> TeamInviteAcceptResult:
        result: TeamInviteAcceptResult | None = None
        expired_error: TeamInviteExpiredError | None = None

        async with self._session_factory() as session:
            try:
                async with session.begin():
                    invite = await _lock_invite(session, token_hash)
                    expired_error = _validate_invite_state(invite, now)
                    if expired_error is None:
                        email = invite.invited_email
                        existing_user = await session.scalar(
                            select(UserAccount.id).where(UserAccount.email == email)
                        )
                        if existing_user is not None:
                            raise TeamInviteUserExistsError(
                                "Account already exists for this invite. "
                                "Please log in to accept."
                            )

                        user_id = uuid4()
                        user = UserAccount(
                            id=user_id,
                            email=email,
                            password_hash=password_hash,
                            password_pepper_version=password_pepper_version,
                            status=DBUserStatus.ACTIVE,
                            email_verified_at=now,
                        )
                        session.add(user)

                        if display_name:
                            session.add(
                                UserProfile(
                                    id=uuid4(),
                                    user_id=user_id,
                                    display_name=display_name,
                                )
                            )

                        session.add(
                            TenantUserMembership(
                                id=uuid4(),
                                user_id=user_id,
                                tenant_id=invite.tenant_id,
                                role=invite.role,
                            )
                        )

                        session.add(
                            PasswordHistory(
                                id=uuid4(),
                                user_id=user_id,
                                password_hash=password_hash,
                                password_pepper_version=password_pepper_version,
                                created_at=now,
                            )
                        )

                        _mark_invite_accepted(invite, user_id=user_id, now=now)

                        result = TeamInviteAcceptResult(
                            invite_id=invite.id,
                            user_id=user_id,
                            tenant_id=invite.tenant_id,
                            email=email,
                        )
            except IntegrityError as exc:
                raise TeamInviteUserExistsError(
                    "Account already exists for this invite. Please log in to accept."
                ) from exc

        if expired_error is not None:
            raise expired_error
        if result is None:
            raise TeamInviteValidationError("Invite acceptance did not complete.")
        return result

    async def accept_for_existing_user(
        self,
        *,
        token_hash: str,
        user_id: UUID,
        now: datetime,
    ) -> TeamInvite:
        accepted_invite: TeamInvite | None = None
        expired_error: TeamInviteExpiredError | None = None

        async with self._session_factory() as session:
            try:
                async with session.begin():
                    invite = await _lock_invite(session, token_hash)
                    expired_error = _validate_invite_state(invite, now)
                    if expired_error is None:
                        user = await session.get(UserAccount, user_id)
                        if user is None:
                            raise TeamInviteNotFoundError("User not found.")
                        if user.email.lower() != invite.invited_email.lower():
                            raise TeamInviteEmailMismatchError(
                                "Invite email does not match current user."
                            )

                        existing_membership = await session.scalar(
                            select(TenantUserMembership.id).where(
                                TenantUserMembership.tenant_id == invite.tenant_id,
                                TenantUserMembership.user_id == user_id,
                            )
                        )
                        if existing_membership is not None:
                            raise TeamMemberAlreadyExistsError(
                                "User is already a member of this tenant."
                            )

                        session.add(
                            TenantUserMembership(
                                id=uuid4(),
                                user_id=user_id,
                                tenant_id=invite.tenant_id,
                                role=invite.role,
                            )
                        )
                        user.email_verified_at = now

                        _mark_invite_accepted(invite, user_id=user_id, now=now)
                        accepted_invite = _to_domain_invite(invite)
            except IntegrityError as exc:
                raise TeamMemberAlreadyExistsError(
                    "User is already a member of this tenant."
                ) from exc

        if expired_error is not None:
            raise expired_error
        if accepted_invite is None:
            raise TeamInviteValidationError("Invite acceptance did not complete.")
        return accepted_invite


async def _lock_invite(
    session: AsyncSession,
    token_hash: str,
) -> TenantMemberInvite:
    invite = await session.scalar(
        select(TenantMemberInvite)
        .where(TenantMemberInvite.token_hash == token_hash)
        .with_for_update()
    )
    if invite is None:
        raise TeamInviteNotFoundError("Invite token is invalid.")
    return invite


def _validate_invite_state(
    invite: TenantMemberInvite,
    now: datetime,
) -> TeamInviteExpiredError | None:
    if invite.status == TeamInviteStatus.REVOKED:
        raise TeamInviteRevokedError("Invite has been revoked.")
    if invite.status == TeamInviteStatus.ACCEPTED:
        raise TeamInviteRevokedError("Invite has already been accepted.")
    if invite.status == TeamInviteStatus.EXPIRED:
        return TeamInviteExpiredError("Invite has expired.")
    expires_at = invite.expires_at
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at and expires_at <= now:
        invite.status = TeamInviteStatus.EXPIRED
        invite.revoked_at = now
        invite.revoked_reason = "expired"
        invite.updated_at = now
        return TeamInviteExpiredError("Invite has expired.")
    return None


def _mark_invite_accepted(invite: TenantMemberInvite, *, user_id: UUID, now: datetime) -> None:
    invite.status = TeamInviteStatus.ACCEPTED
    invite.accepted_by_user_id = user_id
    invite.accepted_at = now
    invite.updated_at = now


def _to_domain_invite(invite: TenantMemberInvite) -> TeamInvite:
    return TeamInvite(
        id=invite.id,
        tenant_id=invite.tenant_id,
        token_hash=invite.token_hash,
        token_hint=invite.token_hint,
        invited_email=invite.invited_email,
        role=invite.role,
        status=invite.status,
        created_by_user_id=invite.created_by_user_id,
        accepted_by_user_id=invite.accepted_by_user_id,
        accepted_at=invite.accepted_at,
        revoked_at=invite.revoked_at,
        revoked_reason=invite.revoked_reason,
        expires_at=invite.expires_at,
        created_at=invite.created_at,
        updated_at=invite.updated_at,
    )


def get_team_invite_acceptance_repository(
    settings: Settings | None = None,
) -> TeamInviteAcceptanceRepository | None:
    resolved_settings = settings or get_settings()
    if not resolved_settings.database_url:
        return None
    try:
        session_factory = get_async_sessionmaker()
    except RuntimeError:
        return None
    return PostgresTeamInviteAcceptanceRepository(session_factory)


__all__ = [
    "PostgresTeamInviteAcceptanceRepository",
    "get_team_invite_acceptance_repository",
]
