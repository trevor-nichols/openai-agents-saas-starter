"""High-level helpers for persisting user session metadata."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.domain.auth import (
    SessionLocation,
    UserSession,
    UserSessionListResult,
    UserSessionRepository,
)
from app.observability.logging import log_event
from app.services.geoip_service import GeoIPService
from app.utils.user_agent import summarize_user_agent


class SessionStore:
    """Encapsulates session persistence plus optional GeoIP enrichment."""

    def __init__(
        self,
        repository: UserSessionRepository | None,
        geoip_service: GeoIPService | None,
    ) -> None:
        self._repository = repository
        self._geoip_service = geoip_service

    def require_repository(self) -> UserSessionRepository:
        if not self._repository:
            raise RuntimeError("User session repository not configured.")
        return self._repository

    async def upsert(
        self,
        *,
        session_id: UUID,
        user_id: UUID,
        tenant_id: UUID,
        refresh_jti: str,
        fingerprint: str | None,
        ip_address: str | None,
        user_agent: str | None,
        occurred_at: datetime,
    ) -> None:
        if not self._repository:
            return
        client = summarize_user_agent(user_agent)
        location = await self._resolve_session_location(ip_address)
        try:
            await self._repository.upsert_session(
                session_id=session_id,
                user_id=user_id,
                tenant_id=tenant_id,
                refresh_jti=refresh_jti,
                fingerprint=fingerprint,
                ip_address=ip_address,
                user_agent=user_agent,
                client=client,
                location=location,
                occurred_at=occurred_at,
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            log_event(
                "auth.session_record",
                level="warning",
                result="failure",
                reason="repository_error",
                detail=str(exc),
            )

    async def list_sessions(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID | None,
        include_revoked: bool,
        limit: int,
        offset: int,
    ) -> UserSessionListResult:
        repo = self.require_repository()
        return await repo.list_sessions(
            user_id=user_id,
            tenant_id=tenant_id,
            include_revoked=include_revoked,
            limit=limit,
            offset=offset,
        )

    async def get_session(self, *, session_id: UUID, user_id: UUID) -> UserSession | None:
        repo = self.require_repository()
        return await repo.get_session(session_id=session_id, user_id=user_id)

    async def mark_session_revoked(self, *, session_id: UUID, reason: str) -> None:
        repo = self.require_repository()
        await repo.mark_session_revoked(session_id=session_id, reason=reason)

    async def mark_session_revoked_by_jti(self, *, refresh_jti: str, reason: str) -> None:
        if not self._repository:
            return
        await self._repository.mark_session_revoked_by_jti(refresh_jti=refresh_jti, reason=reason)

    async def revoke_all_for_user(self, *, user_id: UUID, reason: str) -> None:
        if not self._repository:
            return
        await self._repository.revoke_all_for_user(user_id=user_id, reason=reason)

    async def _resolve_session_location(self, ip_address: str | None) -> SessionLocation | None:
        if not ip_address or not self._geoip_service:
            return None
        try:
            return await self._geoip_service.lookup(ip_address)
        except Exception as exc:  # pragma: no cover - geo providers are optional
            log_event(
                "auth.session_geo_lookup",
                level="warning",
                result="failure",
                detail=str(exc),
            )
            return None
