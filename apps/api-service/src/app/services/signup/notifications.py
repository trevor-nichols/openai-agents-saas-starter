"""Signup notification dispatchers."""

from __future__ import annotations

from app.observability.logging import log_event
from app.services.signup.email_verification_service import (
    EmailVerificationService,
    get_email_verification_service,
)


class SignupNotificationService:
    def __init__(self, *, email_verification: EmailVerificationService | None = None) -> None:
        self._email_verification = email_verification

    def _get_email_verification(self) -> EmailVerificationService:
        if self._email_verification is None:
            self._email_verification = get_email_verification_service()
        return self._email_verification

    async def send_email_verification(
        self,
        *,
        user_id: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        try:
            service = self._get_email_verification()
            await service.send_verification_email(
                user_id=user_id,
                email=None,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except Exception as exc:  # pragma: no cover - best effort
            log_event(
                "signup.email_verification",
                result="error",
                user_id=user_id,
                reason=str(exc),
            )


__all__ = ["SignupNotificationService"]
