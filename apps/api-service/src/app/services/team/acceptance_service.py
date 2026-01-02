"""Service for accepting tenant member invites without UI or delivery concerns."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app.core.normalization import normalize_email
from app.core.security import PASSWORD_HASH_VERSION, get_password_hash
from app.core.settings import Settings, get_settings
from app.domain.team import (
    TeamInviteAcceptanceRepository,
    TeamInviteRepository,
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
from app.domain.users import UserRecord, UserRepository
from app.infrastructure.persistence.auth.team_invite_acceptance_repository import (
    get_team_invite_acceptance_repository,
)
from app.infrastructure.persistence.auth.team_invite_repository import (
    get_team_invite_repository,
)
from app.infrastructure.persistence.auth.user_repository import get_user_repository


@dataclass(slots=True)
class TeamInviteAcceptanceResult:
    invite_id: UUID
    user: UserRecord
    created_user: bool
    accepted_at: datetime


class TeamInviteAcceptanceError(RuntimeError):
    """Base error for invite acceptance workflows."""


class TeamInviteRequiredError(TeamInviteAcceptanceError):
    """Raised when no eligible invite exists for the email."""


class TeamInviteInvalidError(TeamInviteAcceptanceError):
    """Raised when invite validation fails for all candidates."""


class TeamInviteAcceptanceService:
    def __init__(
        self,
        *,
        invite_repository: TeamInviteRepository,
        acceptance_repository: TeamInviteAcceptanceRepository,
        user_repository: UserRepository,
    ) -> None:
        self._invite_repository = invite_repository
        self._acceptance_repository = acceptance_repository
        self._user_repository = user_repository

    async def accept_best_invite(
        self,
        *,
        tenant_id: UUID,
        email: str,
        existing_user: UserRecord | None,
        display_name: str | None,
        now: datetime | None = None,
        max_candidates: int = 10,
    ) -> TeamInviteAcceptanceResult:
        timestamp = now or datetime.now(UTC)
        normalized_email = normalize_email(email)
        if not normalized_email:
            raise TeamInviteRequiredError("Invite email is required.")
        invites = await self._invite_repository.list_invites(
            tenant_id=tenant_id,
            status=TeamInviteStatus.ACTIVE,
            email=normalized_email,
            limit=max_candidates,
            offset=0,
        )
        candidates = sorted(invites.invites, key=lambda invite: invite.created_at, reverse=True)
        if not candidates:
            raise TeamInviteRequiredError("An active invite is required for SSO.")

        last_error: Exception | None = None
        for invite in candidates:
            try:
                if existing_user:
                    try:
                        await self._acceptance_repository.accept_for_existing_user(
                            token_hash=invite.token_hash,
                            user_id=existing_user.id,
                            now=timestamp,
                        )
                    except TeamMemberAlreadyExistsError:
                        await self._invite_repository.mark_accepted(
                            invite.id,
                            timestamp=timestamp,
                            accepted_by_user_id=existing_user.id,
                        )
                    return TeamInviteAcceptanceResult(
                        invite_id=invite.id,
                        user=existing_user,
                        created_user=False,
                        accepted_at=timestamp,
                    )

                try:
                    password_seed = secrets.token_urlsafe(32)
                    result = await self._acceptance_repository.accept_for_new_user(
                        token_hash=invite.token_hash,
                        password_hash=get_password_hash(password_seed),
                        password_pepper_version=PASSWORD_HASH_VERSION,
                        display_name=display_name,
                        now=timestamp,
                    )
                    created = await self._user_repository.get_user_by_id(result.user_id)
                    if created is None:
                        raise TeamInviteInvalidError("Failed to load provisioned user.")
                    return TeamInviteAcceptanceResult(
                        invite_id=invite.id,
                        user=created,
                        created_user=True,
                        accepted_at=timestamp,
                    )
                except TeamInviteUserExistsError:
                    existing = await self._user_repository.get_user_by_email(
                        normalized_email
                    )
                    if existing is None:
                        raise
                    try:
                        await self._acceptance_repository.accept_for_existing_user(
                            token_hash=invite.token_hash,
                            user_id=existing.id,
                            now=timestamp,
                        )
                    except TeamMemberAlreadyExistsError:
                        await self._invite_repository.mark_accepted(
                            invite.id,
                            timestamp=timestamp,
                            accepted_by_user_id=existing.id,
                        )
                    return TeamInviteAcceptanceResult(
                        invite_id=invite.id,
                        user=existing,
                        created_user=False,
                        accepted_at=timestamp,
                    )
            except (
                TeamInviteExpiredError,
                TeamInviteNotFoundError,
                TeamInviteRevokedError,
                TeamInviteEmailMismatchError,
                TeamInviteUserExistsError,
                TeamInviteValidationError,
            ) as exc:
                last_error = exc
                continue

        if last_error is not None:
            raise TeamInviteInvalidError(
                "Invite validation failed for acceptance.") from last_error
        raise TeamInviteRequiredError("An active invite is required for SSO.")


def build_team_invite_acceptance_service(
    *, settings: Settings | None = None
) -> TeamInviteAcceptanceService:
    resolved_settings = settings or get_settings()
    invite_repository = get_team_invite_repository(resolved_settings)
    acceptance_repository = get_team_invite_acceptance_repository(resolved_settings)
    user_repository = get_user_repository(resolved_settings)
    if invite_repository is None:
        raise RuntimeError("Team invite repository is not configured.")
    if acceptance_repository is None:
        raise RuntimeError("Team invite acceptance repository is not configured.")
    if user_repository is None:
        raise RuntimeError("User repository is not configured.")
    return TeamInviteAcceptanceService(
        invite_repository=invite_repository,
        acceptance_repository=acceptance_repository,
        user_repository=user_repository,
    )


__all__ = [
    "TeamInviteAcceptanceError",
    "TeamInviteAcceptanceResult",
    "TeamInviteAcceptanceService",
    "TeamInviteInvalidError",
    "TeamInviteRequiredError",
    "build_team_invite_acceptance_service",
]
