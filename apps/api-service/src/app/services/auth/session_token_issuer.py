"""Issue access/refresh tokens for user sessions."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.core.security import get_token_signer
from app.core.settings import Settings, get_settings
from app.domain.users import AuthenticatedUser


@dataclass(frozen=True, slots=True)
class IssuedSessionTokens:
    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime
    access_kid: str
    refresh_kid: str
    access_jti: str
    refresh_jti: str
    session_id: UUID
    fingerprint: str | None
    account: str
    issued_at: datetime


def issue_session_tokens(
    auth_user: AuthenticatedUser,
    *,
    ip_address: str | None,
    user_agent: str | None,
    session_id: UUID | None = None,
    settings: Settings | None = None,
) -> IssuedSessionTokens:
    resolved_settings = settings or get_settings()
    signer = get_token_signer(resolved_settings)
    issued_at = datetime.now(UTC)
    access_expires = issued_at + timedelta(minutes=resolved_settings.access_token_expire_minutes)
    audience = resolved_settings.auth_audience or [resolved_settings.app_name]
    session_uuid = session_id or uuid4()
    fingerprint = build_session_fingerprint(ip_address, user_agent)
    access_jti = str(uuid4())

    access_payload = {
        "sub": f"user:{auth_user.user_id}",
        "tenant_id": str(auth_user.tenant_id),
        "roles": [auth_user.role.value],
        "scope": " ".join(auth_user.scopes),
        "token_use": "access",
        "iss": resolved_settings.app_name,
        "aud": audience,
        "jti": access_jti,
        "email_verified": auth_user.email_verified,
        "sid": str(session_uuid),
        "iat": int(issued_at.timestamp()),
        "nbf": int(issued_at.timestamp()),
        "exp": int(access_expires.timestamp()),
    }
    signed_access = signer.sign(access_payload)

    refresh_ttl = getattr(resolved_settings, "auth_refresh_token_ttl_minutes", 43200)
    refresh_expires = issued_at + timedelta(minutes=refresh_ttl)
    account = f"user:{auth_user.user_id}"
    refresh_jti = str(uuid4())
    refresh_payload = {
        "sub": f"user:{auth_user.user_id}",
        "tenant_id": str(auth_user.tenant_id),
        "scope": " ".join(auth_user.scopes),
        "token_use": "refresh",
        "iss": resolved_settings.app_name,
        "email_verified": auth_user.email_verified,
        "jti": refresh_jti,
        "iat": int(issued_at.timestamp()),
        "nbf": int(issued_at.timestamp()),
        "exp": int(refresh_expires.timestamp()),
        "account": account,
        "sid": str(session_uuid),
    }
    signed_refresh = signer.sign(refresh_payload)

    return IssuedSessionTokens(
        access_token=signed_access.primary.token,
        refresh_token=signed_refresh.primary.token,
        access_expires_at=access_expires,
        refresh_expires_at=refresh_expires,
        access_kid=signed_access.primary.kid,
        refresh_kid=signed_refresh.primary.kid,
        access_jti=access_jti,
        refresh_jti=refresh_jti,
        session_id=session_uuid,
        fingerprint=fingerprint,
        account=account,
        issued_at=issued_at,
    )


def build_session_fingerprint(ip_address: str | None, user_agent: str | None) -> str | None:
    if not ip_address and not user_agent:
        return None
    material = f"{ip_address or ''}:{user_agent or ''}"
    encoded = base64.urlsafe_b64encode(material.encode("utf-8")).rstrip(b"=")
    return encoded.decode("utf-8")
