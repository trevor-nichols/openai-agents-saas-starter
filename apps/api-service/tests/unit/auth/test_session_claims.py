"""Unit tests for session claim parsing helpers."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.services.auth.errors import UserAuthenticationError, UserRefreshError
from app.services.auth.session_claims import (
    MfaChallengeClaims,
    RefreshTokenClaims,
    parse_mfa_challenge_claims,
    parse_refresh_claims,
)


def _user_subject(user_id: UUID) -> str:
    return f"user:{user_id}"


def test_parse_refresh_claims_success() -> None:
    user_id = uuid4()
    session_id = uuid4()
    payload: dict[str, object] = {
        "token_use": "refresh",
        "sub": _user_subject(user_id),
        "tenant_id": "tenant-123",
        "jti": "refresh-jti",
        "sid": str(session_id),
    }

    claims = parse_refresh_claims(payload, error_cls=UserRefreshError, require_tenant=True)

    assert isinstance(claims, RefreshTokenClaims)
    assert claims.user_id == user_id
    assert claims.tenant_id == "tenant-123"
    assert claims.jti == "refresh-jti"
    assert claims.session_id == session_id


def test_parse_refresh_claims_allows_missing_tenant_when_optional() -> None:
    user_id = uuid4()
    payload: dict[str, object] = {
        "token_use": "refresh",
        "sub": _user_subject(user_id),
        "jti": "refresh-jti",
    }

    claims = parse_refresh_claims(payload, error_cls=UserRefreshError, require_tenant=False)

    assert claims.user_id == user_id
    assert claims.tenant_id is None
    assert claims.jti == "refresh-jti"


def test_parse_refresh_claims_rejects_missing_tenant() -> None:
    payload: dict[str, object] = {
        "token_use": "refresh",
        "sub": _user_subject(uuid4()),
        "jti": "refresh-jti",
    }

    with pytest.raises(UserRefreshError):
        parse_refresh_claims(payload, error_cls=UserRefreshError, require_tenant=True)


def test_parse_refresh_claims_rejects_non_refresh_token() -> None:
    payload: dict[str, object] = {
        "token_use": "access",
        "sub": _user_subject(uuid4()),
        "tenant_id": "tenant-123",
        "jti": "refresh-jti",
    }

    with pytest.raises(UserRefreshError):
        parse_refresh_claims(payload, error_cls=UserRefreshError, require_tenant=True)


def test_parse_mfa_challenge_claims_success() -> None:
    user_id = uuid4()
    session_id = uuid4()
    payload: dict[str, object] = {
        "token_use": "mfa_challenge",
        "sub": _user_subject(user_id),
        "tenant_id": "tenant-123",
        "sid": str(session_id),
        "login_reason": "sso",
    }

    claims = parse_mfa_challenge_claims(payload, error_cls=UserAuthenticationError)

    assert isinstance(claims, MfaChallengeClaims)
    assert claims.user_id == user_id
    assert claims.tenant_id == "tenant-123"
    assert claims.session_id == session_id
    assert claims.login_reason == "sso"


def test_parse_mfa_challenge_claims_defaults_login_reason() -> None:
    user_id = uuid4()
    session_id = uuid4()
    payload: dict[str, object] = {
        "token_use": "mfa_challenge",
        "sub": _user_subject(user_id),
        "tenant_id": "tenant-123",
        "sid": str(session_id),
    }

    claims = parse_mfa_challenge_claims(payload, error_cls=UserAuthenticationError)

    assert claims.login_reason == "login"


def test_parse_mfa_challenge_claims_rejects_invalid_subject() -> None:
    payload: dict[str, object] = {
        "token_use": "mfa_challenge",
        "sub": "service-account:analytics",
        "tenant_id": "tenant-123",
        "sid": str(uuid4()),
    }

    with pytest.raises(UserAuthenticationError):
        parse_mfa_challenge_claims(payload, error_cls=UserAuthenticationError)
