"""Helper for storing and querying refresh tokens."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID, uuid4

import jwt

from app.domain.auth import RefreshTokenRecord, RefreshTokenRepository


class RefreshTokenManager:
    """Wraps a RefreshTokenRepository with convenience helpers."""

    def __init__(self, repository: RefreshTokenRepository | None) -> None:
        self._repository = repository

    @property
    def is_configured(self) -> bool:
        return self._repository is not None

    async def find_active(
        self,
        *,
        account: str,
        tenant_id: str | None,
        scopes: Sequence[str],
    ) -> RefreshTokenRecord | None:
        repo = self._get_repository(require=False)
        if not repo:
            return None
        return await repo.find_active(account, tenant_id, scopes)

    async def save(
        self,
        *,
        token: str,
        account: str,
        tenant_id: str | None,
        scopes: list[str],
        issued_at: datetime,
        expires_at: datetime,
        fingerprint: str | None,
        signing_kid: str,
        session_id: UUID | None,
        jti: str | None = None,
        require: bool = True,
    ) -> None:
        repo = self._get_repository(require=require)
        if not repo:
            return
        record = RefreshTokenRecord(
            token=token,
            jti=jti or self._extract_jti(token),
            account=account,
            tenant_id=tenant_id,
            scopes=scopes,
            expires_at=expires_at,
            issued_at=issued_at,
            fingerprint=fingerprint,
            signing_kid=signing_kid,
            session_id=session_id,
        )
        await repo.save(record)

    async def get_by_jti(self, jti: str, *, require: bool = True) -> RefreshTokenRecord | None:
        repo = self._get_repository(require=require)
        if not repo:
            return None
        return await repo.get_by_jti(jti)

    async def revoke(self, jti: str, *, reason: str | None = None, require: bool = True) -> None:
        repo = self._get_repository(require=require)
        if not repo:
            return
        await repo.revoke(jti, reason=reason)

    async def revoke_account(self, account: str, *, reason: str, require: bool = True) -> int:
        repo = self._get_repository(require=require)
        if not repo:
            return 0
        return await repo.revoke_account(account, reason=reason)

    def record_to_response(
        self, record: RefreshTokenRecord
    ) -> dict[str, str | int | list[str] | None]:
        kid = record.signing_kid or self._extract_kid(record.token)
        return {
            "refresh_token": record.token,
            "expires_at": record.expires_at.isoformat(),
            "issued_at": record.issued_at.isoformat(),
            "scopes": record.scopes,
            "tenant_id": record.tenant_id,
            "kid": kid,
            "account": record.account,
            "token_use": "refresh",
            "session_id": str(record.session_id) if record.session_id else None,
        }

    def _extract_jti(self, token: str) -> str:
        try:
            payload = jwt.decode(token, options={"verify_signature": False, "verify_exp": False})
        except Exception:
            return str(uuid4())
        value = payload.get("jti")
        return str(value) if value else str(uuid4())

    def _extract_kid(self, token: str) -> str:
        try:
            header = jwt.get_unverified_header(token)
        except Exception:
            return "unknown"
        kid = header.get("kid")
        return str(kid) if kid else "unknown"

    def _get_repository(self, *, require: bool) -> RefreshTokenRepository | None:
        if not self._repository and require:
            raise RuntimeError("Refresh-token repository is not configured.")
        return self._repository
