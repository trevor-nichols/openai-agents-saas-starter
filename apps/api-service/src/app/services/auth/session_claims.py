"""Helpers for parsing JWT claim payloads used in session flows."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from .errors import UserAuthenticationError


@dataclass(frozen=True, slots=True)
class RefreshTokenClaims:
    user_id: UUID
    tenant_id: str | None
    jti: str
    session_id: UUID | None


@dataclass(frozen=True, slots=True)
class MfaChallengeClaims:
    user_id: UUID
    tenant_id: str
    session_id: UUID
    login_reason: str


def parse_refresh_claims(
    payload: dict[str, object],
    *,
    error_cls: type[UserAuthenticationError],
    require_tenant: bool,
) -> RefreshTokenClaims:
    if payload.get("token_use") != "refresh":
        raise error_cls("Token is not a refresh token.")

    subject = _require_str(
        payload, "sub", error_cls=error_cls, error_message="Refresh token subject is malformed."
    )
    user_id = _parse_user_subject(
        subject, error_cls=error_cls, error_message="Refresh token subject is malformed."
    )

    tenant_id: str | None
    if require_tenant:
        tenant_id = _require_str(
            payload,
            "tenant_id",
            error_cls=error_cls,
            error_message="Refresh token missing tenant identifier.",
        )
    else:
        tenant_id_value = payload.get("tenant_id")
        tenant_id = tenant_id_value if isinstance(tenant_id_value, str) else None

    jti = _require_str(
        payload, "jti", error_cls=error_cls, error_message="Refresh token missing jti claim."
    )
    session_id = _parse_session_id(payload.get("sid"))
    return RefreshTokenClaims(user_id=user_id, tenant_id=tenant_id, jti=jti, session_id=session_id)


def parse_mfa_challenge_claims(
    payload: dict[str, object],
    *,
    error_cls: type[UserAuthenticationError],
) -> MfaChallengeClaims:
    if payload.get("token_use") != "mfa_challenge":
        raise error_cls("Invalid MFA challenge token.")

    subject = _require_str(
        payload, "sub", error_cls=error_cls, error_message="Challenge token subject is malformed."
    )
    user_id = _parse_user_subject(
        subject, error_cls=error_cls, error_message="Challenge token subject is malformed."
    )
    tenant_id = _require_str(
        payload,
        "tenant_id",
        error_cls=error_cls,
        error_message="Challenge token missing tenant id.",
    )
    session_id_raw = _require_str(
        payload,
        "sid",
        error_cls=error_cls,
        error_message="Challenge token missing session id.",
    )
    try:
        session_id = UUID(session_id_raw)
    except ValueError as exc:  # pragma: no cover - defensive
        raise error_cls("Challenge token session id is invalid.") from exc

    login_reason_value = payload.get("login_reason")
    if isinstance(login_reason_value, str) and login_reason_value.strip():
        login_reason = login_reason_value.strip()
    else:
        login_reason = "login"

    return MfaChallengeClaims(
        user_id=user_id,
        tenant_id=tenant_id,
        session_id=session_id,
        login_reason=login_reason,
    )


def _require_str(
    payload: dict[str, object],
    key: str,
    *,
    error_cls: type[UserAuthenticationError],
    error_message: str,
) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise error_cls(error_message)
    return value


def _parse_user_subject(
    subject: str,
    *,
    error_cls: type[UserAuthenticationError],
    error_message: str,
) -> UUID:
    if not subject.startswith("user:"):
        raise error_cls(error_message)
    try:
        return UUID(subject.split("user:", 1)[1])
    except ValueError as exc:  # pragma: no cover - defensive
        raise error_cls(error_message) from exc


def _parse_session_id(value: object) -> UUID | None:
    if not isinstance(value, str):
        return None
    try:
        return UUID(value)
    except ValueError:  # pragma: no cover - defensive
        return None
