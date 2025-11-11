"""Password recovery orchestration service."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import uuid4

from app.core.config import Settings, get_settings
from app.domain.password_reset import PasswordResetTokenRecord, PasswordResetTokenStore
from app.domain.users import UserRecord, UserRepository
from app.infrastructure.notifications import (
    ResendEmailAdapter,
    ResendEmailError,
    ResendEmailRequest,
    get_resend_email_adapter,
)
from app.infrastructure.persistence.auth.user_repository import get_user_repository
from app.infrastructure.security.password_reset_store import get_password_reset_token_store
from app.observability.logging import log_event
from app.presentation.emails import render_password_reset_email
from app.services.auth_service import auth_service
from app.services.user_service import (
    InvalidCredentialsError,
    PasswordPolicyViolationError,
    PasswordReuseError,
    UserService,
    get_user_service,
)


class PasswordRecoveryError(RuntimeError):
    """Base class for password recovery failures."""


class PasswordResetDeliveryError(PasswordRecoveryError):
    """Raised when the password reset email cannot be delivered."""


class InvalidPasswordResetTokenError(PasswordRecoveryError):
    """Raised when a password reset token is invalid or expired."""


class PasswordResetNotifier(Protocol):
    async def send_password_reset(
        self,
        *,
        email: str,
        token: str,
        expires_at: datetime,
    ) -> None:
        ...


@dataclass(slots=True)
class LoggingPasswordResetNotifier(PasswordResetNotifier):
    async def send_password_reset(self, *, email: str, token: str, expires_at: datetime) -> None:
        log_event(
            "auth.password_reset_notification",
            result="queued",
            email=email,
            expires_at=expires_at.isoformat(),
            token_preview=f"{token[:4]}...",
        )


class ResendPasswordResetNotifier(PasswordResetNotifier):
    def __init__(self, adapter: ResendEmailAdapter, settings: Settings) -> None:
        self._adapter = adapter
        self._settings = settings

    async def send_password_reset(self, *, email: str, token: str, expires_at: datetime) -> None:
        request = self._build_request(email=email, token=token, expires_at=expires_at)
        try:
            await self._adapter.send_email(request)
        except ResendEmailError as exc:
            log_event(
                "auth.password_reset_notification",
                result="error",
                email=email,
                reason=getattr(exc, "error_code", None) or "resend_error",
            )
            raise PasswordResetDeliveryError("Failed to send password reset email.") from exc

    def _build_request(
        self,
        *,
        email: str,
        token: str,
        expires_at: datetime,
    ) -> ResendEmailRequest:
        subject = f"Reset your {self._settings.app_name} password"
        template_id = self._settings.resend_password_reset_template_id
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
                tags={"category": "password_reset"},
                category="password_reset",
            )

        content = render_password_reset_email(self._settings, token, expires_at)
        return ResendEmailRequest(
            to=[email],
            subject=subject,
            html_body=content.html,
            text_body=content.text,
            tags={"category": "password_reset"},
            category="password_reset",
        )


class PasswordRecoveryService:
    def __init__(
        self,
        user_repository: UserRepository,
        token_store: PasswordResetTokenStore,
        notifier: PasswordResetNotifier,
        *,
        settings: Settings | None = None,
        user_service: UserService | None = None,
    ) -> None:
        self._repository = user_repository
        self._token_store = token_store
        self._notifier = notifier
        self._settings = settings or get_settings()
        self._user_service = user_service

    async def request_password_reset(
        self,
        *,
        email: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        normalized_email = email.strip().lower()
        user = await self._repository.get_user_by_email(normalized_email)
        if not user:
            log_event(
                "auth.password_reset_request",
                result="ignored",
                reason="unknown_email",
                email=normalized_email,
            )
            return

        token, record = self._mint_token(user, ip_address, user_agent)
        ttl_seconds = self._token_ttl_seconds()
        await self._token_store.save(record, ttl_seconds=ttl_seconds)
        await self._notifier.send_password_reset(
            email=user.email,
            token=token,
            expires_at=record.expires_at,
        )
        log_event(
            "auth.password_reset_request",
            result="queued",
            user_id=str(user.id),
            token_id=record.token_id,
        )

    async def confirm_password_reset(
        self,
        *,
        token: str,
        new_password: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        token_id, secret = self._split_token(token)
        record = await self._token_store.get(token_id)
        if not record:
            raise InvalidPasswordResetTokenError("Password reset token is invalid or expired.")

        if not self._verify_secret(secret, record.hashed_secret):
            raise InvalidPasswordResetTokenError("Password reset token is invalid or expired.")

        service = self._user_service or get_user_service()
        try:
            await service.reset_password_via_token(
                user_id=record.user_id,
                new_password=new_password,
            )
        except InvalidCredentialsError as exc:
            await self._token_store.delete(token_id)
            log_event(
                "auth.password_reset",
                result="failure",
                reason="user_missing",
                token_id=record.token_id,
            )
            raise InvalidPasswordResetTokenError(
                "Password reset token is invalid or expired."
            ) from exc
        except (PasswordPolicyViolationError, PasswordReuseError):
            # Keep the token so the caller can retry with a compliant password.
            raise
        except Exception:
            # Defensive: prevent token reuse if the downstream operation fails unexpectedly.
            await self._token_store.delete(token_id)
            raise
        else:
            await self._token_store.delete(token_id)

        await auth_service.revoke_user_sessions(record.user_id, reason="password_reset_token")
        log_event(
            "auth.password_reset",
            result="success",
            user_id=str(record.user_id),
            token_id=record.token_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def _mint_token(
        self,
        user: UserRecord,
        ip_address: str | None,
        user_agent: str | None,
    ) -> tuple[str, PasswordResetTokenRecord]:
        token_id = uuid4().hex
        secret = secrets.token_hex(32)
        composite = f"{token_id}.{secret}"
        issued_at = datetime.now(UTC)
        expires_at = issued_at + timedelta(minutes=self._settings.password_reset_token_ttl_minutes)
        record = PasswordResetTokenRecord(
            token_id=token_id,
            user_id=user.id,
            email=user.email,
            hashed_secret=self._hash_secret(secret),
            created_at=issued_at,
            expires_at=expires_at,
            fingerprint=self._fingerprint(ip_address, user_agent),
        )
        return composite, record

    def _token_ttl_seconds(self) -> int:
        minutes = max(int(self._settings.password_reset_token_ttl_minutes), 1)
        return minutes * 60

    def _split_token(self, value: str) -> tuple[str, str]:
        if not value or "." not in value:
            raise InvalidPasswordResetTokenError("Password reset token is malformed.")
        token_id, secret = value.split(".", 1)
        if not token_id or not secret:
            raise InvalidPasswordResetTokenError("Password reset token is malformed.")
        return token_id, secret

    def _hash_secret(self, secret: str) -> str:
        material = f"{self._token_pepper()}:{secret}".encode()
        return hashlib.sha256(material).hexdigest()

    def _verify_secret(self, secret: str, hashed: str) -> bool:
        return hmac.compare_digest(self._hash_secret(secret), hashed)

    def _fingerprint(self, ip_address: str | None, user_agent: str | None) -> str | None:
        if not ip_address and not user_agent:
            return None
        material = f"{ip_address or ''}:{user_agent or ''}"
        digest = hashlib.sha256(material.encode("utf-8"))
        return digest.hexdigest()

    def _token_pepper(self) -> str:
        pepper = getattr(self._settings, "auth_password_reset_token_pepper", None)
        if not pepper:
            raise RuntimeError("AUTH_PASSWORD_RESET_TOKEN_PEPPER must be configured.")
        return pepper


def build_password_recovery_service(
    *,
    settings: Settings | None = None,
    repository: UserRepository | None = None,
    token_store: PasswordResetTokenStore | None = None,
    notifier: PasswordResetNotifier | None = None,
    user_service: UserService | None = None,
) -> PasswordRecoveryService:
    resolved_settings = settings or get_settings()
    resolved_repository = repository or get_user_repository(resolved_settings)
    if resolved_repository is None:
        raise RuntimeError("User repository is not configured; password reset unavailable.")
    resolved_token_store = token_store or get_password_reset_token_store(resolved_settings)
    resolved_notifier: PasswordResetNotifier
    if notifier is not None:
        resolved_notifier = notifier
    elif resolved_settings.enable_resend_email_delivery:
        adapter = get_resend_email_adapter(resolved_settings)
        resolved_notifier = ResendPasswordResetNotifier(adapter, resolved_settings)
    else:
        resolved_notifier = LoggingPasswordResetNotifier()

    return PasswordRecoveryService(
        resolved_repository,
        resolved_token_store,
        resolved_notifier,
        settings=resolved_settings,
        user_service=user_service,
    )


__all__ = [
    "InvalidPasswordResetTokenError",
    "PasswordResetDeliveryError",
    "PasswordRecoveryError",
    "PasswordRecoveryService",
    "build_password_recovery_service",
    "get_password_recovery_service",
]


def get_password_recovery_service() -> PasswordRecoveryService:
    from app.bootstrap.container import get_container

    container = get_container()
    if container.password_recovery_service is None:
        container.password_recovery_service = build_password_recovery_service(
            user_service=container.user_service
        )
    return container.password_recovery_service
