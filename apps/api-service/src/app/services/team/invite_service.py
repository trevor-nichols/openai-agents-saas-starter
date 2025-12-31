"""Tenant member invite service."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.core.password_policy import PasswordPolicyError, validate_password_strength
from app.core.security import PASSWORD_HASH_VERSION, get_password_hash
from app.core.settings import get_settings
from app.domain.team import (
    TeamInvite,
    TeamInviteAcceptanceRepository,
    TeamInviteAcceptResult,
    TeamInviteCreate,
    TeamInviteListResult,
    TeamInviteRepository,
    TeamInviteStatus,
    TenantMembershipRepository,
)
from app.domain.team_errors import (
    TeamInviteDeliveryError,
    TeamInviteExpiredError,
    TeamInviteNotFoundError,
    TeamInviteRevokedError,
    TeamInviteValidationError,
    TeamMemberAlreadyExistsError,
)
from app.domain.team_policy import TEAM_INVITE_POLICY
from app.domain.tenant_accounts import TenantAccountRepository
from app.domain.tenant_roles import TenantRole
from app.domain.users import UserRepository
from app.infrastructure.notifications import ResendEmailError, get_resend_email_adapter
from app.infrastructure.persistence.auth.team_invite_acceptance_repository import (
    get_team_invite_acceptance_repository,
)
from app.infrastructure.persistence.auth.team_invite_repository import (
    get_team_invite_repository,
)
from app.infrastructure.persistence.auth.user_repository import get_user_repository
from app.infrastructure.persistence.tenants.account_repository import (
    get_tenant_account_repository,
)
from app.observability.logging import log_event

from .invite_notifier import (
    LoggingTeamInviteNotifier,
    ResendTeamInviteNotifier,
    TeamInviteNotifier,
)
from .roles import ensure_owner_role_change_allowed, normalize_team_role


@dataclass(slots=True)
class TeamInviteIssueResult:
    invite: TeamInvite
    invite_token: str


class TeamInviteService:
    def __init__(
        self,
        *,
        invite_repository: TeamInviteRepository,
        acceptance_repository: TeamInviteAcceptanceRepository,
        user_repository: UserRepository,
        membership_repository: TenantMembershipRepository,
        tenant_repository: TenantAccountRepository,
        notifier: TeamInviteNotifier | None,
    ) -> None:
        self._invite_repository = invite_repository
        self._acceptance_repository = acceptance_repository
        self._user_repository = user_repository
        self._membership_repository = membership_repository
        self._tenant_repository = tenant_repository
        self._notifier = notifier

    async def issue_invite(
        self,
        *,
        tenant_id: UUID,
        invited_email: str,
        role: TenantRole,
        created_by_user_id: UUID | None,
        actor_role: TenantRole,
        expires_in_hours: int | None = TEAM_INVITE_POLICY.default_expires_hours,
    ) -> TeamInviteIssueResult:
        normalized_role = normalize_team_role(role)
        ensure_owner_role_change_allowed(
            actor_role=actor_role,
            target_role=normalized_role,
        )
        if expires_in_hours is not None and not (
            1 <= expires_in_hours <= TEAM_INVITE_POLICY.max_expires_hours
        ):
            raise TeamInviteValidationError(
                "Invite expiry must be between 1 and "
                f"{TEAM_INVITE_POLICY.max_expires_hours} hours."
            )
        normalized_email = _normalize_email(invited_email)

        existing_user = await self._user_repository.get_user_by_email(normalized_email)
        if existing_user is not None:
            already_member = await self._membership_repository.membership_exists(
                tenant_id=tenant_id,
                user_id=existing_user.id,
            )
            if already_member:
                raise TeamMemberAlreadyExistsError(
                    "User is already a member of this tenant."
                )

        token = secrets.token_urlsafe(32)
        hashed = _hash_token(token)
        expires_at = (
            datetime.now(UTC) + timedelta(hours=expires_in_hours)
            if expires_in_hours
            else None
        )

        invite = await self._invite_repository.create(
            TeamInviteCreate(
                tenant_id=tenant_id,
                token_hash=hashed,
                token_hint=_token_hint(token),
                invited_email=normalized_email,
                role=normalized_role,
                created_by_user_id=created_by_user_id,
                expires_at=expires_at,
            )
        )

        await self._send_invite_email(invite=invite, token=token)
        log_event(
            "team.invite_issued",
            result="success",
            invite_id=str(invite.id),
            tenant_id=str(invite.tenant_id),
            user_id=str(created_by_user_id) if created_by_user_id else None,
        )
        return TeamInviteIssueResult(invite=invite, invite_token=token)

    async def list_invites(
        self,
        *,
        tenant_id: UUID,
        status: TeamInviteStatus | None = None,
        email: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> TeamInviteListResult:
        return await self._invite_repository.list_invites(
            tenant_id=tenant_id,
            status=status,
            email=_normalize_email(email) if email else None,
            limit=limit,
            offset=offset,
        )

    async def revoke_invite(
        self,
        invite_id: UUID,
        *,
        tenant_id: UUID,
        actor_user_id: UUID | None = None,
        reason: str | None = None,
    ) -> TeamInvite:
        timestamp = datetime.now(UTC)
        record = await self._invite_repository.mark_revoked(
            invite_id,
            tenant_id=tenant_id,
            timestamp=timestamp,
            reason=reason,
        )
        if record is None:
            existing = await self._invite_repository.get(invite_id)
            if existing is None or existing.tenant_id != tenant_id:
                raise TeamInviteNotFoundError("Invite not found.")
            raise TeamInviteRevokedError("Invite is no longer active.")
        log_event(
            "team.invite_revoked",
            result="success",
            invite_id=str(record.id),
            tenant_id=str(record.tenant_id),
            user_id=str(actor_user_id) if actor_user_id else None,
        )
        return record

    async def accept_invite_for_new_user(
        self,
        *,
        token: str,
        password: str,
        display_name: str | None,
    ) -> TeamInviteAcceptResult:
        return await self._accept_invite_for_new_user(
            token=token,
            password=password,
            display_name=display_name,
        )

    async def accept_invite_for_existing_user(
        self,
        *,
        token: str,
        user_id: UUID,
    ) -> TeamInvite:
        return await self._accept_invite_for_existing_user(
            token=token,
            user_id=user_id,
        )

    async def _accept_invite_for_new_user(
        self,
        *,
        token: str,
        password: str,
        display_name: str | None,
    ) -> TeamInviteAcceptResult:
        if not token:
            raise TeamInviteNotFoundError("Invite token is required.")
        hashed_token = _hash_token(token)
        now = datetime.now(UTC)

        invite = await self._invite_repository.find_by_token_hash(hashed_token)
        if invite is None:
            raise TeamInviteNotFoundError("Invite token is invalid.")
        if invite.status == TeamInviteStatus.REVOKED:
            raise TeamInviteRevokedError("Invite has been revoked.")
        if invite.status == TeamInviteStatus.ACCEPTED:
            raise TeamInviteRevokedError("Invite has already been accepted.")
        if invite.status == TeamInviteStatus.EXPIRED:
            raise TeamInviteExpiredError("Invite has expired.")
        expires_at = invite.expires_at
        if expires_at is not None and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at and expires_at <= now:
            expired = await self._invite_repository.mark_expired(invite.id, timestamp=now)
            if expired is not None:
                raise TeamInviteExpiredError("Invite has expired.")
        try:
            validate_password_strength(password, user_inputs=[invite.invited_email])
        except PasswordPolicyError as exc:
            raise TeamInviteValidationError(str(exc)) from exc

        result = await self._acceptance_repository.accept_for_new_user(
            token_hash=hashed_token,
            password_hash=get_password_hash(password),
            password_pepper_version=PASSWORD_HASH_VERSION,
            display_name=display_name,
            now=now,
        )

        log_event(
            "team.invite_accepted",
            result="success",
            invite_id=str(result.invite_id),
            tenant_id=str(result.tenant_id),
            user_id=str(result.user_id),
        )
        return result

    async def _accept_invite_for_existing_user(
        self,
        *,
        token: str,
        user_id: UUID,
    ) -> TeamInvite:
        if not token:
            raise TeamInviteNotFoundError("Invite token is required.")
        hashed_token = _hash_token(token)
        now = datetime.now(UTC)

        accepted_invite = await self._acceptance_repository.accept_for_existing_user(
            token_hash=hashed_token,
            user_id=user_id,
            now=now,
        )

        log_event(
            "team.invite_accepted",
            result="success",
            invite_id=str(accepted_invite.id),
            tenant_id=str(accepted_invite.tenant_id),
            user_id=str(user_id),
        )
        return accepted_invite

    async def _send_invite_email(self, *, invite: TeamInvite, token: str) -> None:
        if self._notifier is None:
            return
        tenant_name = await self._resolve_tenant_name(invite.tenant_id)
        try:
            await self._notifier.send_invite(
                email=invite.invited_email,
                token=token,
                tenant_name=tenant_name,
                role=invite.role.value,
                expires_at=invite.expires_at,
            )
        except ResendEmailError as exc:
            revoked = await self._invite_repository.mark_revoked(
                invite.id,
                tenant_id=invite.tenant_id,
                timestamp=datetime.now(UTC),
                reason="delivery_failed",
            )
            if revoked is not None:
                log_event(
                    "team.invite_revoked",
                    result="success",
                    invite_id=str(revoked.id),
                    tenant_id=str(revoked.tenant_id),
                    user_id=(
                        str(revoked.created_by_user_id)
                        if revoked.created_by_user_id
                        else None
                    ),
                    reason="delivery_failed",
                )
            raise TeamInviteDeliveryError("Failed to deliver invite email.") from exc

    async def _resolve_tenant_name(self, tenant_id: UUID) -> str:
        name = await self._tenant_repository.get_name(tenant_id)
        return str(name or "your team")


def _hash_token(token: str) -> str:
    digest = hashlib.sha256(token.strip().encode("utf-8")).hexdigest()
    return digest


def _token_hint(token: str) -> str:
    return token[:8]


def _normalize_email(value: str | None) -> str:
    if value is None:
        raise TeamInviteValidationError("Invite email is required.")
    normalized = value.strip().lower()
    if not normalized:
        raise TeamInviteValidationError("Invite email is required.")
    return normalized


def build_team_invite_service(
    *,
    invite_repository: TeamInviteRepository | None = None,
    acceptance_repository: TeamInviteAcceptanceRepository | None = None,
    membership_repository: TenantMembershipRepository | None = None,
    user_repository: UserRepository | None = None,
    tenant_repository: TenantAccountRepository | None = None,
) -> TeamInviteService:
    settings = get_settings()
    resolved_invite_repo = invite_repository or get_team_invite_repository(settings)
    if resolved_invite_repo is None:
        raise RuntimeError("Team invite repository is not configured.")
    resolved_acceptance_repo = acceptance_repository or get_team_invite_acceptance_repository(
        settings
    )
    if resolved_acceptance_repo is None:
        raise RuntimeError("Team invite acceptance repository is not configured.")
    resolved_membership_repo = membership_repository
    if resolved_membership_repo is None:
        from app.infrastructure.persistence.auth.membership_repository import (
            get_tenant_membership_repository,
        )

        resolved_membership_repo = get_tenant_membership_repository(settings)
    if resolved_membership_repo is None:
        raise RuntimeError("Tenant membership repository is not configured.")

    resolved_user_repo = user_repository or get_user_repository(settings)
    if resolved_user_repo is None:
        raise RuntimeError("User repository is not configured.")

    resolved_tenant_repo = tenant_repository or get_tenant_account_repository(settings)
    if resolved_tenant_repo is None:
        raise RuntimeError("Tenant account repository is not configured.")

    notifier: TeamInviteNotifier
    if settings.enable_resend_email_delivery:
        adapter = get_resend_email_adapter(settings)
        notifier = ResendTeamInviteNotifier(adapter, settings)
    else:
        notifier = LoggingTeamInviteNotifier()

    return TeamInviteService(
        invite_repository=resolved_invite_repo,
        acceptance_repository=resolved_acceptance_repo,
        user_repository=resolved_user_repo,
        membership_repository=resolved_membership_repo,
        tenant_repository=resolved_tenant_repo,
        notifier=notifier,
    )


def get_team_invite_service() -> TeamInviteService:
    from app.bootstrap.container import get_container

    container = get_container()
    if container.team_invite_service is None:
        container.team_invite_service = build_team_invite_service()
    return container.team_invite_service


__all__ = [
    "TeamInviteAcceptResult",
    "TeamInviteIssueResult",
    "TeamInviteService",
    "build_team_invite_service",
    "get_team_invite_service",
]
