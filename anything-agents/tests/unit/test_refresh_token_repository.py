"""Regression tests for refresh-token rehydration."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace, MethodType
from uuid import uuid4

from app.core.config import Settings
from app.infrastructure.persistence.auth import repository as repository_module
from app.infrastructure.persistence.auth.repository import PostgresRefreshTokenRepository


UTC = timezone.utc


def _build_repo() -> PostgresRefreshTokenRepository:
    settings = Settings(app_name="unit-tests", auth_refresh_token_pepper="unit-pepper")

    # session_factory is never invoked in these unit tests; provide a stub callable.
    repo = PostgresRefreshTokenRepository(lambda: None, settings)  # type: ignore[arg-type]
    return repo


def test_rehydrate_service_account_token_includes_original_claims(monkeypatch) -> None:
    repo = _build_repo()
    issued_at = datetime.now(UTC).replace(microsecond=0)
    expires_at = issued_at + timedelta(minutes=30)
    tenant_id = uuid4()
    expected_token = "signed-token-service"
    expected_payload = {
        "sub": "service-account:analytics-batch",
        "account": "analytics-batch",
        "token_use": "refresh",
        "jti": "jti-service",
        "scope": "conversations:read",
        "iss": repo._settings.app_name,
        "iat": int(issued_at.timestamp()),
        "nbf": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
        "tenant_id": str(tenant_id),
        "fingerprint": "fp",
    }

    row = SimpleNamespace(
        account="analytics-batch",
        refresh_jti="jti-service",
        scopes=["conversations:read"],
        issued_at=issued_at,
        expires_at=expires_at,
        tenant_id=tenant_id,
        fingerprint="fp",
        signing_kid="kid-1",
        refresh_token_hash="stored-hash-service",
        scope_key="conversations:read",
    )

    def fake_encode(self, payload, signing_kid):  # type: ignore[no-untyped-def]
        assert payload == expected_payload
        assert signing_kid == "kid-1"
        return expected_token

    monkeypatch.setattr(
        repo,
        "_encode_with_signing_kid",
        MethodType(fake_encode, repo),
    )

    new_verify = lambda token, hashed, pepper: token == expected_token and hashed == "stored-hash-service"  # noqa: E731
    monkeypatch.setattr(
        repository_module,
        "verify_refresh_token",
        new_verify,
    )
    assert repository_module.verify_refresh_token is new_verify

    record = repo._row_to_record(row)
    assert record is not None
    assert record.token == expected_token


def test_rehydrate_user_token_preserves_user_subject(monkeypatch) -> None:
    repo = _build_repo()
    issued_at = datetime.now(UTC).replace(microsecond=0)
    expires_at = issued_at + timedelta(minutes=45)
    tenant_id = uuid4()
    account = f"user:{uuid4()}"
    expected_token = "signed-token-user"
    expected_payload = {
        "sub": account,
        "account": account,
        "token_use": "refresh",
        "jti": "jti-user",
        "scope": "conversations:write",
        "iss": repo._settings.app_name,
        "iat": int(issued_at.timestamp()),
        "nbf": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
        "tenant_id": str(tenant_id),
    }

    row = SimpleNamespace(
        account=account,
        refresh_jti="jti-user",
        scopes=["conversations:write"],
        issued_at=issued_at,
        expires_at=expires_at,
        tenant_id=tenant_id,
        fingerprint=None,
        signing_kid="kid-2",
        refresh_token_hash="stored-hash-user",
        scope_key="conversations:write",
    )

    def fake_encode(self, payload, signing_kid):  # type: ignore[no-untyped-def]
        assert payload == expected_payload
        assert signing_kid == "kid-2"
        return expected_token

    monkeypatch.setattr(
        repo,
        "_encode_with_signing_kid",
        MethodType(fake_encode, repo),
    )

    new_verify = lambda token, hashed, pepper: token == expected_token and hashed == "stored-hash-user"  # noqa: E731
    monkeypatch.setattr(
        repository_module,
        "verify_refresh_token",
        new_verify,
    )
    assert repository_module.verify_refresh_token is new_verify

    record = repo._row_to_record(row)
    assert record is not None
    assert record.token == expected_token
