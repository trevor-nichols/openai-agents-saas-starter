"""Unit tests for MFA challenge issuance."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

import pytest

from app.core.security import get_token_verifier
from app.domain.tenant_roles import TenantRole
from app.domain.users import AuthenticatedUser
from app.infrastructure.persistence.auth.models.mfa import MfaMethodType, UserMfaMethod
from app.services.auth.mfa_service import MfaService
from app.services.auth.mfa_challenge_service import MfaChallengeService


class _StubMfaService:
    def __init__(self, methods: list[UserMfaMethod]) -> None:
        self._methods = methods

    async def list_methods(self, user_id: UUID) -> list[UserMfaMethod]:
        return [method for method in self._methods if method.user_id == user_id]


def _build_method(
    *,
    user_id: UUID,
    verified: bool,
    revoked: bool,
    label: str | None = "Device",
) -> UserMfaMethod:
    now = datetime.now(UTC)
    return UserMfaMethod(
        id=uuid4(),
        user_id=user_id,
        method_type=MfaMethodType.TOTP,
        label=label,
        secret_encrypted=None,
        credential_json=None,
        verified_at=now if verified else None,
        last_used_at=now if verified else None,
        revoked_at=now if revoked else None,
        revoked_reason="revoked" if revoked else None,
        created_at=now,
        updated_at=now,
    )


def _build_user(user_id: UUID, tenant_id: UUID) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=user_id,
        tenant_id=tenant_id,
        email="user@example.com",
        role=TenantRole.MEMBER,
        scopes=["conversations:read"],
        email_verified=True,
    )


@pytest.mark.asyncio
async def test_mfa_challenge_issued_for_verified_method() -> None:
    user_id = uuid4()
    tenant_id = uuid4()
    method = _build_method(user_id=user_id, verified=True, revoked=False)
    service = MfaChallengeService(mfa_service=cast(MfaService, _StubMfaService([method])))

    challenge = await service.maybe_issue_challenge(
        _build_user(user_id, tenant_id),
        ip_address=None,
        user_agent=None,
    )

    assert challenge is not None
    assert isinstance(challenge.token, str)
    assert len(challenge.methods) == 1
    payload = challenge.methods[0]
    assert payload["method_type"] == "totp"
    assert payload["label"] == "Device"
    assert payload["verified_at"] is not None

    claims = get_token_verifier().verify(challenge.token)
    assert claims["token_use"] == "mfa_challenge"
    assert claims["sub"] == f"user:{user_id}"
    assert claims["tenant_id"] == str(tenant_id)
    assert "sid" in claims


@pytest.mark.asyncio
async def test_mfa_challenge_skips_unverified_methods() -> None:
    user_id = uuid4()
    tenant_id = uuid4()
    method = _build_method(user_id=user_id, verified=False, revoked=False)
    service = MfaChallengeService(mfa_service=cast(MfaService, _StubMfaService([method])))

    challenge = await service.maybe_issue_challenge(
        _build_user(user_id, tenant_id),
        ip_address=None,
        user_agent=None,
    )

    assert challenge is None


@pytest.mark.asyncio
async def test_mfa_challenge_skips_revoked_methods() -> None:
    user_id = uuid4()
    tenant_id = uuid4()
    method = _build_method(user_id=user_id, verified=True, revoked=True)
    service = MfaChallengeService(mfa_service=cast(MfaService, _StubMfaService([method])))

    challenge = await service.maybe_issue_challenge(
        _build_user(user_id, tenant_id),
        ip_address=None,
        user_agent=None,
    )

    assert challenge is None
