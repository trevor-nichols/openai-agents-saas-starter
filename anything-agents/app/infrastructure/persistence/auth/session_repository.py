"""Postgres-backed repository for user session metadata."""

from __future__ import annotations

import hashlib
import ipaddress
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.domain.auth import (
    SessionClientDetails,
    SessionLocation,
    UserSession,
    UserSessionListResult,
    UserSessionRepository,
)
from app.infrastructure.db import get_async_sessionmaker
from app.infrastructure.persistence.auth.models import UserSession as UserSessionModel
from app.infrastructure.security.cipher import build_cipher, encrypt_optional


class PostgresUserSessionRepository(UserSessionRepository):
    """Composite repository storing session metadata with optional encryption."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        settings: Settings,
    ) -> None:
        self._session_factory = session_factory
        self._hash_salt = (settings.auth_session_ip_hash_salt or settings.secret_key or "").encode(
            "utf-8"
        )
        secret = settings.auth_session_encryption_key or settings.secret_key
        self._cipher = build_cipher(secret)

    async def upsert_session(
        self,
        *,
        session_id: UUID,
        user_id: UUID,
        tenant_id: UUID,
        refresh_jti: str,
        fingerprint: str | None,
        ip_address: str | None,
        user_agent: str | None,
        client: SessionClientDetails,
        location: SessionLocation | None,
        occurred_at: datetime,
    ) -> UserSession:
        normalized_ip = self._normalize_ip(ip_address)
        masked_ip = self._mask_ip(normalized_ip)
        ip_hash = self._hash_ip(normalized_ip)
        encrypted_ip = self._encrypt_ip(normalized_ip)
        now = (
            occurred_at.astimezone(UTC)
            if occurred_at.tzinfo
            else occurred_at.replace(tzinfo=UTC)
        )

        async with self._session_factory() as session:
            record = await session.get(UserSessionModel, session_id)
            if record is None:
                record = UserSessionModel(
                    id=session_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    refresh_jti=refresh_jti,
                    created_at=now,
                )
                session.add(record)

            record.refresh_jti = refresh_jti
            record.fingerprint = fingerprint
            record.user_agent = user_agent
            record.client_platform = client.platform
            record.client_browser = client.browser
            record.client_device = client.device
            record.ip_hash = ip_hash
            record.ip_masked = masked_ip
            record.ip_encrypted = encrypted_ip
            if location:
                record.location_city = location.city
                record.location_region = location.region
                record.location_country = location.country
            record.last_seen_at = now
            record.revoked_at = None
            record.revoked_reason = None
            record.updated_at = now
            await session.commit()
            await session.refresh(record)
        domain = self._to_domain(record)
        if domain is None:  # pragma: no cover - defensive
            raise RuntimeError("Failed to persist user session metadata.")
        return domain

    async def list_sessions(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID | None = None,
        include_revoked: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> UserSessionListResult:
        filters: list[Any] = [UserSessionModel.user_id == user_id]
        if tenant_id:
            filters.append(UserSessionModel.tenant_id == tenant_id)
        if not include_revoked:
            filters.append(UserSessionModel.revoked_at.is_(None))

        async with self._session_factory() as session:
            count_stmt = select(func.count()).where(*filters)
            total = (await session.execute(count_stmt)).scalar_one()

            stmt = (
                select(UserSessionModel)
                .where(*filters)
                .order_by(
                    UserSessionModel.last_seen_at.desc().nullslast(),
                    UserSessionModel.created_at.desc(),
                )
                .offset(offset)
                .limit(limit)
            )
            rows = (await session.execute(stmt)).scalars().all()

        sessions: list[UserSession] = []
        for row in rows:
            domain = self._to_domain(row)
            if domain:
                sessions.append(domain)
        return UserSessionListResult(sessions=sessions, total=total)

    async def get_session(self, *, session_id: UUID, user_id: UUID) -> UserSession | None:
        async with self._session_factory() as session:
            stmt = select(UserSessionModel).where(
                UserSessionModel.id == session_id, UserSessionModel.user_id == user_id
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def mark_session_revoked(
        self,
        *,
        session_id: UUID,
        reason: str | None = None,
    ) -> bool:
        timestamp = datetime.now(UTC)
        async with self._session_factory() as session:
            stmt = (
                update(UserSessionModel)
                .where(UserSessionModel.id == session_id, UserSessionModel.revoked_at.is_(None))
                .values(revoked_at=timestamp, revoked_reason=reason, updated_at=timestamp)
            )
            result = await session.execute(stmt)
            cursor = cast(CursorResult[Any], result)
            await session.commit()
        return (cursor.rowcount or 0) > 0

    async def mark_session_revoked_by_jti(
        self,
        *,
        refresh_jti: str,
        reason: str | None = None,
    ) -> bool:
        timestamp = datetime.now(UTC)
        async with self._session_factory() as session:
            stmt = (
                update(UserSessionModel)
                .where(
                    UserSessionModel.refresh_jti == refresh_jti,
                    UserSessionModel.revoked_at.is_(None),
                )
                .values(revoked_at=timestamp, revoked_reason=reason, updated_at=timestamp)
            )
            result = await session.execute(stmt)
            cursor = cast(CursorResult[Any], result)
            await session.commit()
        return (cursor.rowcount or 0) > 0

    async def revoke_all_for_user(
        self,
        *,
        user_id: UUID,
        reason: str | None = None,
    ) -> int:
        timestamp = datetime.now(UTC)
        async with self._session_factory() as session:
            stmt = (
                update(UserSessionModel)
                .where(UserSessionModel.user_id == user_id, UserSessionModel.revoked_at.is_(None))
                .values(revoked_at=timestamp, revoked_reason=reason, updated_at=timestamp)
            )
            result = await session.execute(stmt)
            cursor = cast(CursorResult[Any], result)
            await session.commit()
        return cursor.rowcount or 0

    def _to_domain(self, row: UserSessionModel | None) -> UserSession | None:
        if row is None:
            return None
        client = SessionClientDetails(
            platform=row.client_platform,
            browser=row.client_browser,
            device=row.client_device,
        )
        location = (
            SessionLocation(
                city=row.location_city,
                region=row.location_region,
                country=row.location_country,
            )
            if any([row.location_city, row.location_region, row.location_country])
            else None
        )
        return UserSession(
            id=row.id,
            user_id=row.user_id,
            tenant_id=row.tenant_id,
            refresh_jti=row.refresh_jti,
            fingerprint=row.fingerprint,
            ip_hash=row.ip_hash,
            ip_masked=row.ip_masked,
            user_agent=row.user_agent,
            client=client,
            location=location,
            created_at=row.created_at,
            updated_at=row.updated_at,
            last_seen_at=row.last_seen_at,
            revoked_at=row.revoked_at,
        )

    def _mask_ip(self, value: str | None) -> str | None:
        if not value:
            return None
        try:
            ip_obj = ipaddress.ip_address(value)
        except ValueError:
            return None
        if ip_obj.version == 4:
            octets = ip_obj.exploded.split(".")
            octets[-1] = "*"
            return ".".join(octets)
        hextets = ip_obj.exploded.split(":")
        masked = hextets[:4] + ["*"] * 4
        return ":".join(masked)

    def _hash_ip(self, value: str | None) -> str | None:
        if not value:
            return None
        digest = hashlib.sha256(self._hash_salt + value.encode("utf-8")).hexdigest()
        return digest

    def _encrypt_ip(self, value: str | None) -> bytes | None:
        return encrypt_optional(self._cipher, value)

    def _normalize_ip(self, value: str | None) -> str | None:
        if not value:
            return None
        candidate = value.split(",")[0].strip()
        return candidate or None


def get_user_session_repository(settings: Settings | None = None) -> UserSessionRepository | None:
    settings = settings or get_settings()
    if not settings.database_url:
        return None
    try:
        session_factory = get_async_sessionmaker()
    except RuntimeError:
        return None
    return PostgresUserSessionRepository(session_factory, settings)
