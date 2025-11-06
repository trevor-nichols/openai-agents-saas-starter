"""Postgres-backed refresh token repository with Redis caching."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Sequence

from jose import jwt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.domain.auth import (
    RefreshTokenRecord,
    RefreshTokenRepository,
    hash_refresh_token,
    make_scope_key,
    verify_refresh_token,
)
from app.infrastructure.db import get_async_sessionmaker
from app.infrastructure.persistence.auth.cache import (
    NullRefreshTokenCache,
    RefreshTokenCache,
    build_refresh_token_cache,
)
from app.infrastructure.persistence.auth.models import ServiceAccountToken

logger = logging.getLogger(__name__)


class PostgresRefreshTokenRepository(RefreshTokenRepository):
    """Composite repository persisting refresh tokens to Postgres with Redis cache."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        settings: Settings,
        cache: RefreshTokenCache | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._cache = cache or NullRefreshTokenCache()
        self._settings = settings
        self._pepper = settings.auth_refresh_token_pepper
        if not self._pepper:
            raise ValueError("AUTH_REFRESH_TOKEN_PEPPER must be configured for refresh-token storage.")

    async def find_active(
        self, account: str, tenant_id: str | None, scopes: Sequence[str]
    ) -> RefreshTokenRecord | None:
        scope_key = make_scope_key(scopes)
        cached = await self._cache.get(account, tenant_id, scope_key)
        if cached:
            return cached

        conditions = [
            ServiceAccountToken.account == account,
            ServiceAccountToken.scope_key == scope_key,
            ServiceAccountToken.revoked_at.is_(None),
            ServiceAccountToken.expires_at > datetime.now(timezone.utc),
        ]
        if tenant_id:
            conditions.append(ServiceAccountToken.tenant_id == uuid.UUID(tenant_id))
        else:
            conditions.append(ServiceAccountToken.tenant_id.is_(None))

        async with self._session_factory() as session:
            result = await session.execute(
                select(ServiceAccountToken)
                .where(*conditions)
                .order_by(ServiceAccountToken.issued_at.desc())
                .limit(1)
            )
            row: ServiceAccountToken | None = result.scalar_one_or_none()

        if not row:
            return None
        record = self._row_to_record(row)
        if not record:
            return None
        await self._cache.set(record)
        return record

    async def save(self, record: RefreshTokenRecord) -> None:
        hashed_token = hash_refresh_token(record.token, pepper=self._pepper)
        async with self._session_factory() as session:
            await self._revoke_existing(
                session, record.account, record.tenant_id, record.scope_key, reason="replaced"
            )
            db_row = ServiceAccountToken(
                id=uuid.uuid4(),
                account=record.account,
                tenant_id=uuid.UUID(record.tenant_id) if record.tenant_id else None,
                scope_key=record.scope_key,
                scopes=record.scopes,
                refresh_token_hash=hashed_token,
                refresh_jti=record.jti,
                fingerprint=record.fingerprint,
                issued_at=record.issued_at,
                expires_at=record.expires_at,
            )
            session.add(db_row)
            await session.commit()
        await self._cache.set(record)

    async def revoke(self, jti: str, *, reason: str | None = None) -> None:
        async with self._session_factory() as session:
            stmt = (
                update(ServiceAccountToken)
                .where(ServiceAccountToken.refresh_jti == jti)
                .values(revoked_at=datetime.now(timezone.utc), revoked_reason=reason)
                .returning(ServiceAccountToken.account, ServiceAccountToken.tenant_id, ServiceAccountToken.scope_key)
            )
            result = await session.execute(stmt)
            await session.commit()

        row = result.first()
        if row:
            tenant = str(row.tenant_id) if row.tenant_id else None
            await self._cache.invalidate(row.account, tenant, row.scope_key)

    async def _revoke_existing(
        self,
        session: AsyncSession,
        account: str,
        tenant_id: str | None,
        scope_key: str,
        *,
        reason: str,
    ) -> None:
        conditions = [
            ServiceAccountToken.account == account,
            ServiceAccountToken.scope_key == scope_key,
            ServiceAccountToken.revoked_at.is_(None),
        ]
        if tenant_id:
            conditions.append(ServiceAccountToken.tenant_id == uuid.UUID(tenant_id))
        else:
            conditions.append(ServiceAccountToken.tenant_id.is_(None))

        await session.execute(
            update(ServiceAccountToken)
            .where(*conditions)
            .values(revoked_at=datetime.now(timezone.utc), revoked_reason=reason)
        )

    def _row_to_record(self, row: ServiceAccountToken) -> RefreshTokenRecord | None:
        token = self._rehydrate_token(row)
        if not token:
            return None
        return RefreshTokenRecord(
            token=token,
            jti=row.refresh_jti,
            account=row.account,
            tenant_id=str(row.tenant_id) if row.tenant_id else None,
            scopes=list(row.scopes),
            expires_at=row.expires_at,
            issued_at=row.issued_at,
            fingerprint=row.fingerprint,
        )

    def _rehydrate_token(self, row: ServiceAccountToken) -> str | None:
        payload = {
            "sub": f"service-account:{row.account}",
            "account": row.account,
            "token_use": "refresh",
            "jti": row.refresh_jti,
            "scope": " ".join(row.scopes),
            "iat": int(row.issued_at.timestamp()),
            "exp": int(row.expires_at.timestamp()),
        }
        if row.tenant_id:
            payload["tenant_id"] = str(row.tenant_id)
        if row.fingerprint:
            payload["fingerprint"] = row.fingerprint
        token = jwt.encode(payload, self._settings.secret_key, algorithm=self._settings.jwt_algorithm)
        if verify_refresh_token(token, row.refresh_token_hash, pepper=self._pepper):
            return token
        logger.warning(
            "Refresh token hash mismatch for account=%s tenant=%s scope_key=%s",
            row.account,
            str(row.tenant_id) if row.tenant_id else "global",
            row.scope_key,
        )
        return None


def get_refresh_token_repository(settings: Settings | None = None) -> RefreshTokenRepository | None:
    settings = settings or get_settings()
    if settings.use_in_memory_repo or not settings.database_url:
        return None
    try:
        session_factory = get_async_sessionmaker()
    except RuntimeError:
        return None
    cache = build_refresh_token_cache(settings)
    return PostgresRefreshTokenRepository(session_factory, settings, cache=cache)
