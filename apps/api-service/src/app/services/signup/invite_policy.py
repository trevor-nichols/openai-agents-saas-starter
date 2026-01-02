"""Policy wrapper for invite-gated signup flows."""

from __future__ import annotations

from collections.abc import Callable

from app.core.settings import Settings, get_settings
from app.services.signup.errors import PublicSignupDisabledError
from app.services.signup.invite_service import (
    InviteEmailMismatchError,
    InviteExpiredError,
    InviteNotFoundError,
    InviteRequestMismatchError,
    InviteReservationContext,
    InviteRevokedError,
    InviteService,
    InviteTokenRequiredError,
    get_invite_service,
)


class SignupInvitePolicyService:
    def __init__(
        self,
        *,
        invite_service: InviteService | None = None,
        settings_factory: Callable[[], Settings] | None = None,
    ) -> None:
        self._invite_service = invite_service
        self._settings_factory = settings_factory or get_settings

    def _get_settings(self) -> Settings:
        return self._settings_factory()

    def _get_invite_service(self) -> InviteService:
        if self._invite_service is None:
            self._invite_service = get_invite_service()
        return self._invite_service

    async def reserve_if_required(
        self,
        *,
        email: str,
        invite_token: str | None,
    ) -> InviteReservationContext | None:
        settings = self._get_settings()
        policy = settings.signup_access_policy
        if policy == "public":
            return None
        try:
            return await self._get_invite_service().reserve_for_signup(
                token=invite_token,
                email=email,
                require_request=policy == "approval",
            )
        except (
            InviteTokenRequiredError,
            InviteExpiredError,
            InviteRequestMismatchError,
            InviteRevokedError,
            InviteNotFoundError,
            InviteEmailMismatchError,
        ) as exc:
            raise PublicSignupDisabledError(str(exc)) from exc


__all__ = ["SignupInvitePolicyService"]
