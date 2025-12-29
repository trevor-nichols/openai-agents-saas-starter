"""Invite email delivery helpers for team management."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.core.settings import Settings
from app.infrastructure.notifications import (
    ResendEmailAdapter,
    ResendEmailError,
    ResendEmailRequest,
)
from app.observability.logging import log_event
from app.presentation.emails import render_team_invite_email


class TeamInviteNotifier(Protocol):
    async def send_invite(
        self,
        *,
        email: str,
        token: str,
        tenant_name: str,
        role: str,
        expires_at: datetime | None,
    ) -> None: ...


@dataclass(slots=True)
class LoggingTeamInviteNotifier(TeamInviteNotifier):
    async def send_invite(
        self,
        *,
        email: str,
        token: str,
        tenant_name: str,
        role: str,
        expires_at: datetime | None,
    ) -> None:
        log_event(
            "team.invite_notification",
            result="queued",
            email=email,
            tenant_name=tenant_name,
            role=role,
            expires_at=expires_at.isoformat() if expires_at else None,
            token_preview=f"{token[:4]}...",
        )


class ResendTeamInviteNotifier(TeamInviteNotifier):
    def __init__(self, adapter: ResendEmailAdapter, settings: Settings) -> None:
        self._adapter = adapter
        self._settings = settings

    async def send_invite(
        self,
        *,
        email: str,
        token: str,
        tenant_name: str,
        role: str,
        expires_at: datetime | None,
    ) -> None:
        request = self._build_request(
            email=email,
            token=token,
            tenant_name=tenant_name,
            role=role,
            expires_at=expires_at,
        )
        try:
            await self._adapter.send_email(request)
        except ResendEmailError as exc:
            log_event(
                "team.invite_notification",
                result="error",
                email=email,
                tenant_name=tenant_name,
                reason=getattr(exc, "error_code", None) or "resend_error",
            )
            raise

    def _build_request(
        self,
        *,
        email: str,
        token: str,
        tenant_name: str,
        role: str,
        expires_at: datetime | None,
    ) -> ResendEmailRequest:
        subject = f"You're invited to join {tenant_name}"
        content = render_team_invite_email(
            self._settings,
            token=token,
            tenant_name=tenant_name,
            role=role,
            expires_at=expires_at,
        )
        return ResendEmailRequest(
            to=[email],
            subject=subject,
            html_body=content.html,
            text_body=content.text,
            tags={"category": "team_invite"},
            category="team_invite",
        )


__all__ = [
    "LoggingTeamInviteNotifier",
    "ResendTeamInviteNotifier",
    "TeamInviteNotifier",
]
