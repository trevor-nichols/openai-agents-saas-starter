"""Regression tests for refresh-token rehydration."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import MethodType
from typing import Any, cast
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql.elements import ColumnElement

from app.core.settings import Settings
from app.domain.auth import ServiceAccountTokenStatus
from app.infrastructure.persistence.auth import repository as repository_module
from app.infrastructure.persistence.auth.models import ServiceAccountToken
from app.infrastructure.persistence.auth.repository import PostgresRefreshTokenRepository

UTC = UTC


def _build_repo() -> PostgresRefreshTokenRepository:
    settings = Settings.model_validate(
        {
            "APP_NAME": "unit-tests",
            "AUTH_REFRESH_TOKEN_PEPPER": "unit-pepper",
        }
    )

    # session_factory is never invoked in these unit tests; provide a stub callable.
    session_factory = cast(async_sessionmaker[AsyncSession], lambda: None)
    repo = PostgresRefreshTokenRepository(session_factory, settings)
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

    row = ServiceAccountToken(
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

    def fake_encode(
        self: PostgresRefreshTokenRepository,
        payload: dict[str, Any],
        signing_kid: str,
    ) -> str:
        assert payload == expected_payload
        assert signing_kid == "kid-1"
        return expected_token

    monkeypatch.setattr(
        repo,
        "_encode_with_signing_kid",
        MethodType(fake_encode, repo),
    )

    def new_verify(token: str, hashed: str, *, pepper: str) -> bool:
        return token == expected_token and hashed == "stored-hash-service"
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

    row = ServiceAccountToken(
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

    def fake_encode(
        self: PostgresRefreshTokenRepository,
        payload: dict[str, Any],
        signing_kid: str,
    ) -> str:
        assert payload == expected_payload
        assert signing_kid == "kid-2"
        return expected_token

    monkeypatch.setattr(
        repo,
        "_encode_with_signing_kid",
        MethodType(fake_encode, repo),
    )

    def new_verify(token: str, hashed: str, *, pepper: str) -> bool:
        return token == expected_token and hashed == "stored-hash-user"
    monkeypatch.setattr(
        repository_module,
        "verify_refresh_token",
        new_verify,
    )
    assert repository_module.verify_refresh_token is new_verify

    record = repo._row_to_record(row)
    assert record is not None
    assert record.token == expected_token


def _compile_where_sql(conditions: list[ColumnElement[bool]]) -> str:
    stmt = select(ServiceAccountToken).where(*conditions)
    return str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))


def test_build_list_conditions_enforces_active_tenant_scope() -> None:
    repo = _build_repo()
    tenant_id = str(uuid4())

    sql = _compile_where_sql(
        repo._build_list_conditions(
            tenant_ids=[tenant_id],
            include_global=False,
            account_query=None,
            fingerprint=None,
            status=ServiceAccountTokenStatus.ACTIVE,
        )
    )

    assert f"tenant_id IN ('{tenant_id}')" in sql
    assert "tenant_id IS NULL" not in sql
    assert "revoked_at IS NULL" in sql
    assert "expires_at >" in sql


def test_build_list_conditions_allows_operator_include_global_and_filters() -> None:
    repo = _build_repo()
    tenant_id = str(uuid4())

    sql = _compile_where_sql(
        repo._build_list_conditions(
            tenant_ids=[tenant_id],
            include_global=True,
            account_query="batch",
            fingerprint="runner",
            status=ServiceAccountTokenStatus.REVOKED,
        )
    )

    assert "tenant_id IN" in sql and "tenant_id IS NULL" in sql
    assert "ILIKE '%%batch%%'" in sql
    assert "fingerprint = 'runner'" in sql
    assert "revoked_at IS NOT NULL" in sql
