"""Issue MFA challenge tokens and format method payloads."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.core.security import get_token_signer
from app.core.settings import Settings, get_settings
from app.domain.users import AuthenticatedUser
from app.infrastructure.persistence.auth.models.mfa import UserMfaMethod
from app.observability.logging import log_event
from app.services.auth.mfa_service import MfaService


@dataclass(frozen=True, slots=True)
class MfaChallenge:
    token: str
    methods: list[dict[str, object]]


@dataclass(frozen=True, slots=True)
class MfaMethodSummary:
    id: UUID
    method_type: str
    label: str | None
    verified_at: str | None
    last_used_at: str | None
    revoked_at: str | None

    @classmethod
    def from_model(cls, method: UserMfaMethod) -> MfaMethodSummary:
        return cls(
            id=method.id,
            method_type=getattr(method.method_type, "value", str(method.method_type)),
            label=method.label,
            verified_at=method.verified_at.isoformat() if method.verified_at else None,
            last_used_at=method.last_used_at.isoformat() if method.last_used_at else None,
            revoked_at=method.revoked_at.isoformat() if method.revoked_at else None,
        )

    def as_payload(self) -> dict[str, object]:
        return {
            "id": self.id,
            "method_type": self.method_type,
            "label": self.label,
            "verified_at": self.verified_at,
            "last_used_at": self.last_used_at,
            "revoked_at": self.revoked_at,
        }


class MfaChallengeService:
    """Builds MFA challenges when verified methods exist."""

    def __init__(
        self,
        *,
        mfa_service: MfaService,
        settings: Settings | None = None,
    ) -> None:
        self._mfa_service = mfa_service
        self._settings = settings or get_settings()

    async def maybe_issue_challenge(
        self,
        auth_user: AuthenticatedUser,
        *,
        ip_address: str | None,
        user_agent: str | None,
        login_reason: str,
    ) -> MfaChallenge | None:
        needs_mfa, methods = await self._requires_mfa(self._mfa_service, auth_user.user_id)
        if not needs_mfa:
            return None
        return self._issue_mfa_challenge(auth_user, methods, login_reason=login_reason)

    def require_mfa_service(self) -> MfaService:
        return self._mfa_service

    async def _requires_mfa(
        self, service: MfaService, user_id: UUID
    ) -> tuple[bool, list[UserMfaMethod]]:
        methods = await service.list_methods(user_id)
        verified = [m for m in methods if m.verified_at and not m.revoked_at]
        return bool(verified), verified

    def _issue_mfa_challenge(
        self,
        auth_user: AuthenticatedUser,
        methods: list[UserMfaMethod],
        *,
        login_reason: str,
    ) -> MfaChallenge:
        issued_at = datetime.now(UTC)
        expires = issued_at + timedelta(minutes=self._settings.mfa_challenge_ttl_minutes)
        session_uuid = uuid4()
        normalized_reason = login_reason.strip() or "login"
        payload = {
            "sub": f"user:{auth_user.user_id}",
            "tenant_id": str(auth_user.tenant_id),
            "token_use": "mfa_challenge",
            "login_reason": normalized_reason,
            "iss": self._settings.app_name,
            "aud": self._settings.auth_audience or [self._settings.app_name],
            "jti": str(uuid4()),
            "sid": str(session_uuid),
            "iat": int(issued_at.timestamp()),
            "nbf": int(issued_at.timestamp()),
            "exp": int(expires.timestamp()),
        }
        token = get_token_signer(self._settings).sign(payload).primary.token
        method_payload = [MfaMethodSummary.from_model(m).as_payload() for m in methods]
        log_event(
            "auth.mfa_challenge",
            result="pending",
            user_id=str(auth_user.user_id),
            tenant_id=str(auth_user.tenant_id),
        )
        return MfaChallenge(token=token, methods=method_payload)
