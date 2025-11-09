"""Service responsible for email verification flows."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID, uuid4

from app.core.config import Settings, get_settings
from app.domain.email_verification import (
    EmailVerificationTokenRecord,
    EmailVerificationTokenStore,
)
from app.domain.users import UserRepository
from app.infrastructure.notifications import (
    ResendEmailAdapter,
    ResendEmailError,
    ResendEmailRequest,
    get_resend_email_adapter,
)
from app.infrastructure.persistence.auth.user_repository import get_user_repository
from app.infrastructure.security.email_verification_store import (
    get_email_verification_token_store,
)
from app.observability.logging import log_event
from app.presentation.emails import render_verification_email
from app.services.auth_service import auth_service


class EmailVerificationError(RuntimeError):
    """Base class for email verification failures."""


class EmailVerificationDeliveryError(EmailVerificationError):
    """Raised when the verification email cannot be delivered."""


class InvalidEmailVerificationTokenError(EmailVerificationError):
    """Raised when a verification token cannot be redeemed."""


class EmailVerificationNotifier(Protocol):
    async def send_verification(
        self,
        *,
        email: str,
        token: str,
        expires_at: datetime,
    ) -> None: ...


@dataclass(slots=True)
class LoggingEmailVerificationNotifier(EmailVerificationNotifier):
    async def send_verification(self, *, email: str, token: str, expires_at: datetime) -> None:
        log_event(
            "auth.email_verification_notification",
            result="queued",
            email=email,
            expires_at=expires_at.isoformat(),
            token_preview=f"{token[:4]}...",
        )


class ResendEmailVerificationNotifier(EmailVerificationNotifier):
    """Sends verification emails through Resend."""

    def __init__(self, adapter: ResendEmailAdapter, settings: Settings) -> None:
        self._adapter = adapter
        self._settings = settings

    async def send_verification(self, *, email: str, token: str, expires_at: datetime) -> None:
        request = self._build_request(email=email, token=token, expires_at=expires_at)
        try:
            await self._adapter.send_email(request)
        except ResendEmailError as exc:
            log_event(
                "auth.email_verification_notification",
                result="error",
                email=email,
                reason=getattr(exc, "error_code", None) or "resend_error",
            )
            raise

    def _build_request(
        self,
        *,
        email: str,
        token: str,
        expires_at: datetime,
    ) -> ResendEmailRequest:
        subject = f"Verify your email for {self._settings.app_name}"
        template_id = self._settings.resend_email_verification_template_id
        if template_id:
            return ResendEmailRequest(
                to=[email],
                subject=subject,
                template_id=template_id,
                template_variables={
                    "token": token,
                    "expires_at": expires_at.isoformat(),
                    "app_name": self._settings.app_name,
                },
                tags={"category": "email_verification"},
                category="email_verification",
            )

        content = render_verification_email(self._settings, token, expires_at)
        return ResendEmailRequest(
            to=[email],
            subject=subject,
            html_body=content.html,
            text_body=content.text,
            tags={"category": "email_verification"},
            category="email_verification",
        )


class EmailVerificationService:
    def __init__(
        self,
        repository: UserRepository,
        token_store: EmailVerificationTokenStore,
        notifier: EmailVerificationNotifier,
        *,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._token_store = token_store
        self._notifier = notifier
        self._settings = settings or get_settings()

    async def send_verification_email(
        self,
        *,
        user_id: str,
        email: str | None = None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> bool:
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            return False
        user = await self._repository.get_user_by_id(user_uuid)
        if user is None:
            return False
        if user.email_verified_at is not None:
            return False
        email_to_use = email or user.email
        token, record = self._mint_token(
            user_id=user.id,
            email=email_to_use,
            ip=ip_address,
            ua=user_agent,
        )
        await self._token_store.save(record, ttl_seconds=self._token_ttl_seconds())
        try:
            await self._notifier.send_verification(
                email=email_to_use,
                token=token,
                expires_at=record.expires_at,
            )
        except ResendEmailError as exc:
            raise EmailVerificationDeliveryError("Failed to send verification email.") from exc
        log_event(
            "auth.email_verification_request",
            result="queued",
            user_id=str(user.id),
            token_id=record.token_id,
        )
        return True

    async def verify_token(
        self,
        *,
        token: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        token_id, secret = self._split_token(token)
        record = await self._token_store.get(token_id)
        if not record:
            raise InvalidEmailVerificationTokenError("Verification token is invalid or expired.")
        if not self._verify_secret(secret, record.hashed_secret):
            raise InvalidEmailVerificationTokenError("Verification token is invalid or expired.")
        await self._token_store.delete(token_id)

        timestamp = datetime.now(UTC)
        await self._repository.mark_email_verified(record.user_id, timestamp=timestamp)
        await auth_service.revoke_user_sessions(record.user_id, reason="email_verified")
        log_event(
            "auth.email_verification",
            result="success",
            user_id=str(record.user_id),
            token_id=record.token_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def _mint_token(
        self,
        *,
        user_id: UUID,
        email: str,
        ip: str | None,
        ua: str | None,
    ) -> tuple[str, EmailVerificationTokenRecord]:
        token_id = uuid4().hex
        secret = secrets.token_hex(32)
        composite = f"{token_id}.{secret}"
        issued_at = datetime.now(UTC)
        expires_at = issued_at + timedelta(
            minutes=self._settings.email_verification_token_ttl_minutes
        )
        fingerprint = self._fingerprint(ip, ua)
        record = EmailVerificationTokenRecord(
            token_id=token_id,
            user_id=user_id,
            email=email,
            hashed_secret=self._hash_secret(secret),
            created_at=issued_at,
            expires_at=expires_at,
            fingerprint=fingerprint,
        )
        return composite, record

    def _token_ttl_seconds(self) -> int:
        return max(int(self._settings.email_verification_token_ttl_minutes) * 60, 60)

    def _split_token(self, value: str) -> tuple[str, str]:
        if not value or "." not in value:
            raise InvalidEmailVerificationTokenError("Verification token is malformed.")
        token_id, secret = value.split(".", 1)
        if not token_id or not secret:
            raise InvalidEmailVerificationTokenError("Verification token is malformed.")
        return token_id, secret

    def _hash_secret(self, secret: str) -> str:
        material = f"{self._settings.auth_email_verification_token_pepper}:{secret}".encode()
        return hashlib.sha256(material).hexdigest()

    def _verify_secret(self, secret: str, hashed: str) -> bool:
        return hmac.compare_digest(self._hash_secret(secret), hashed)

    def _fingerprint(self, ip_address: str | None, user_agent: str | None) -> str | None:
        if not ip_address and not user_agent:
            return None
        material = f"{ip_address or ''}:{user_agent or ''}"
        digest = hashlib.sha256(material.encode())
        return digest.hexdigest()


def build_email_verification_service() -> EmailVerificationService:
    settings = get_settings()
    repository = get_user_repository(settings)
    if repository is None:
        raise RuntimeError("User repository is not configured; email verification unavailable.")
    token_store = get_email_verification_token_store(settings)
    notifier: EmailVerificationNotifier
    if settings.enable_resend_email_delivery:
        adapter = get_resend_email_adapter(settings)
        notifier = ResendEmailVerificationNotifier(adapter, settings)
    else:
        notifier = LoggingEmailVerificationNotifier()
    return EmailVerificationService(repository, token_store, notifier, settings=settings)


_DEFAULT_SERVICE: EmailVerificationService | None = None


def get_email_verification_service() -> EmailVerificationService:
    global _DEFAULT_SERVICE
    if _DEFAULT_SERVICE is None:
        _DEFAULT_SERVICE = build_email_verification_service()
    return _DEFAULT_SERVICE


__all__ = [
    "EmailVerificationDeliveryError",
    "EmailVerificationError",
    "EmailVerificationService",
    "InvalidEmailVerificationTokenError",
    "get_email_verification_service",
]
