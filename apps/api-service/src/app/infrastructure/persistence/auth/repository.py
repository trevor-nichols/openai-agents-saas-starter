"""Postgres-backed refresh token repository with Redis caching."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

import jwt
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.keys import KeyMaterial, load_keyset
from app.core.settings import Settings, get_settings
from app.domain.auth import (
    RefreshTokenRecord,
    RefreshTokenRepository,
    ServiceAccountTokenListResult,
    ServiceAccountTokenStatus,
    ServiceAccountTokenView,
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
from app.infrastructure.persistence.auth.models.sessions import ServiceAccountToken

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
            raise ValueError(
                "AUTH_REFRESH_TOKEN_PEPPER must be configured for refresh-token storage."
            )

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
            ServiceAccountToken.expires_at > datetime.now(UTC),
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

    async def get_by_jti(self, jti: str) -> RefreshTokenRecord | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(ServiceAccountToken).where(ServiceAccountToken.refresh_jti == jti)
            )
            row: ServiceAccountToken | None = result.scalar_one_or_none()

        if not row:
            return None
        if row.revoked_at is not None or row.expires_at <= datetime.now(UTC):
            return None
        return self._row_to_record(row)

    async def save(self, record: RefreshTokenRecord) -> None:
        hashed_token = hash_refresh_token(record.token, pepper=self._pepper)
        enforce_single = self._enforce_single_active(record.account)
        async with self._session_factory() as session:
            if enforce_single:
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
                signing_kid=record.signing_kid or "unknown",
                fingerprint=record.fingerprint,
                session_id=record.session_id,
                issued_at=record.issued_at,
                expires_at=record.expires_at,
            )
            session.add(db_row)
            await session.commit()
        if enforce_single:
            await self._cache.set(record)

    async def revoke(self, jti: str, *, reason: str | None = None) -> None:
        async with self._session_factory() as session:
            stmt = (
                update(ServiceAccountToken)
                .where(ServiceAccountToken.refresh_jti == jti)
                .values(revoked_at=datetime.now(UTC), revoked_reason=reason)
                .returning(
                    ServiceAccountToken.account,
                    ServiceAccountToken.tenant_id,
                    ServiceAccountToken.scope_key,
                )
            )
            result = await session.execute(stmt)
            await session.commit()

        row = result.first()
        if row:
            tenant = str(row.tenant_id) if row.tenant_id else None
            await self._cache.invalidate(row.account, tenant, row.scope_key)

    async def revoke_account(self, account: str, *, reason: str | None = None) -> int:
        async with self._session_factory() as session:
            stmt = (
                update(ServiceAccountToken)
                .where(
                    ServiceAccountToken.account == account,
                    ServiceAccountToken.revoked_at.is_(None),
                )
                .values(revoked_at=datetime.now(UTC), revoked_reason=reason)
                .returning(
                    ServiceAccountToken.account,
                    ServiceAccountToken.tenant_id,
                    ServiceAccountToken.scope_key,
                )
            )
            result = await session.execute(stmt)
            rows = result.fetchall()
            await session.commit()

        for row in rows:
            tenant = str(row.tenant_id) if row.tenant_id else None
            await self._cache.invalidate(row.account, tenant, row.scope_key)
        return len(rows)

    async def list_service_account_tokens(
        self,
        *,
        tenant_ids: Sequence[str] | None,
        include_global: bool,
        account_query: str | None,
        fingerprint: str | None,
        status: ServiceAccountTokenStatus,
        limit: int,
        offset: int,
    ) -> ServiceAccountTokenListResult:
        async with self._session_factory() as session:
            conditions = self._build_list_conditions(
                tenant_ids=tenant_ids,
                include_global=include_global,
                account_query=account_query,
                fingerprint=fingerprint,
                status=status,
            )

            total_stmt = select(func.count()).select_from(ServiceAccountToken).where(*conditions)
            total_result = await session.execute(total_stmt)
            total = int(total_result.scalar_one())

            query = (
                select(ServiceAccountToken)
                .where(*conditions)
                .order_by(ServiceAccountToken.issued_at.desc())
                .limit(limit)
                .offset(offset)
            )
            rows = (await session.execute(query)).scalars().all()

        tokens = [self._row_to_view(row) for row in rows]
        return ServiceAccountTokenListResult(tokens=tokens, total=total)

    def _build_list_conditions(
        self,
        *,
        tenant_ids: Sequence[str] | None,
        include_global: bool,
        account_query: str | None,
        fingerprint: str | None,
        status: ServiceAccountTokenStatus,
    ) -> list[Any]:
        conditions: list[Any] = []

        tenant_filters: list[Any] = []
        if tenant_ids:
            uuid_filters = [uuid.UUID(value) for value in tenant_ids if value]
            if uuid_filters:
                tenant_filters.append(ServiceAccountToken.tenant_id.in_(uuid_filters))
        if include_global:
            tenant_filters.append(ServiceAccountToken.tenant_id.is_(None))
        if tenant_filters:
            conditions.append(or_(*tenant_filters))

        if account_query:
            pattern = f"%{account_query.strip()}%"
            conditions.append(ServiceAccountToken.account.ilike(pattern))

        if fingerprint:
            conditions.append(ServiceAccountToken.fingerprint == fingerprint)

        now = datetime.now(UTC)
        if status == ServiceAccountTokenStatus.ACTIVE:
            conditions.append(ServiceAccountToken.revoked_at.is_(None))
            conditions.append(ServiceAccountToken.expires_at > now)
        elif status == ServiceAccountTokenStatus.REVOKED:
            conditions.append(ServiceAccountToken.revoked_at.is_not(None))

        return conditions

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
            .values(revoked_at=datetime.now(UTC), revoked_reason=reason)
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
            signing_kid=row.signing_kid,
            session_id=row.session_id,
        )

    @staticmethod
    def _row_to_view(row: ServiceAccountToken) -> ServiceAccountTokenView:
        return ServiceAccountTokenView(
            jti=row.refresh_jti,
            account=row.account,
            tenant_id=str(row.tenant_id) if row.tenant_id else None,
            scopes=list(row.scopes),
            expires_at=row.expires_at,
            issued_at=row.issued_at,
            revoked_at=row.revoked_at,
            revoked_reason=row.revoked_reason,
            fingerprint=row.fingerprint,
            signing_kid=row.signing_kid,
        )

    def _rehydrate_token(self, row: ServiceAccountToken) -> str | None:
        subject = self._subject_from_account(row.account)
        payload = {
            "sub": subject,
            "account": row.account,
            "token_use": "refresh",
            "jti": row.refresh_jti,
            "scope": " ".join(row.scopes),
            "iss": self._settings.app_name,
            "iat": int(row.issued_at.timestamp()),
            "nbf": int(row.issued_at.timestamp()),
            "exp": int(row.expires_at.timestamp()),
        }
        if row.tenant_id:
            payload["tenant_id"] = str(row.tenant_id)
        if row.fingerprint:
            payload["fingerprint"] = row.fingerprint
        try:
            token = self._encode_with_signing_kid(payload, row.signing_kid)
        except Exception as exc:
            logger.warning(
                "Unable to reconstruct refresh token for account=%s kid=%s: %s",
                row.account,
                row.signing_kid,
                exc,
            )
            return None
        if verify_refresh_token(token, row.refresh_token_hash, pepper=self._pepper):
            return token
        logger.warning(
            "Refresh token hash mismatch for account=%s tenant=%s scope_key=%s",
            row.account,
            str(row.tenant_id) if row.tenant_id else "global",
            row.scope_key,
        )
        return None

    @staticmethod
    def _subject_from_account(account: str) -> str:
        if account.startswith("user:"):
            return account
        return f"service-account:{account}"

    def _encode_with_signing_kid(self, payload: dict[str, Any], signing_kid: str) -> str:
        material = self._find_key_material(signing_kid)
        if not material or not material.private_key:
            raise RuntimeError(f"Missing key material for kid '{signing_kid}'.")
        headers = {"kid": material.kid, "alg": "EdDSA", "typ": "JWT"}
        encoded = jwt.encode(payload, material.private_key, algorithm="EdDSA", headers=headers)
        return self._ensure_token_str(encoded)

    @staticmethod
    def _ensure_token_str(token: str | bytes) -> str:
        if isinstance(token, bytes):
            return token.decode("utf-8")
        return token

    def _find_key_material(self, kid: str) -> KeyMaterial | None:
        keyset = load_keyset(self._settings)
        candidates: list[KeyMaterial] = []
        if keyset.active:
            candidates.append(keyset.active)

        next_material = getattr(keyset, "next", None)
        if next_material:
            candidates.append(next_material)

        retired_materials = getattr(keyset, "retired", None) or []
        candidates.extend(retired_materials)
        for material in candidates:
            if material.kid == kid:
                return material
        return None

    @staticmethod
    def _enforce_single_active(account: str) -> bool:
        return not account.startswith("user:")


def get_refresh_token_repository(settings: Settings | None = None) -> RefreshTokenRepository | None:
    settings = settings or get_settings()
    if not settings.database_url:
        return None
    try:
        session_factory = get_async_sessionmaker()
    except RuntimeError:
        return None
    cache = build_refresh_token_cache(settings)
    return PostgresRefreshTokenRepository(session_factory, settings, cache=cache)
