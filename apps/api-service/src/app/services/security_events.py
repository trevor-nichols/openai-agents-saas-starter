"""Lightweight security event recorder for auth-related actions."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Select, desc, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.persistence.auth.models.security import SecurityEvent


class SecurityEventService:
    """Persists auditable security events (MFA, password changes, resets, etc.)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def record(
        self,
        *,
        event_type: str,
        user_id: UUID | None = None,
        tenant_id: UUID | None = None,
        source: str | None = None,
        ip_hash: str | None = None,
        user_agent_hash: str | None = None,
        request_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> SecurityEvent:
        event = SecurityEvent(
            id=uuid4(),
            event_type=event_type,
            user_id=user_id,
            tenant_id=tenant_id,
            source=source,
            ip_hash=ip_hash,
            user_agent_hash=user_agent_hash,
            request_id=request_id,
            metadata_json=metadata,
            created_at=datetime.now(UTC),
        )
        async with self._session_factory() as session:
            session.add(event)
            await session.commit()
            await session.refresh(event)
        return event

    async def list_for_tenant(
        self,
        *,
        tenant_id: UUID,
        limit: int = 50,
        before: datetime | None = None,
    ) -> list[SecurityEvent]:
        query: Select[tuple[SecurityEvent]] = select(SecurityEvent).where(
            SecurityEvent.tenant_id == tenant_id
        )
        if before:
            query = query.where(SecurityEvent.created_at < before)
        query = query.order_by(desc(SecurityEvent.created_at)).limit(limit)
        async with self._session_factory() as session:
            result = await session.execute(query)
            return list(result.scalars().all())


def get_security_event_service() -> SecurityEventService:
    from app.bootstrap.container import get_container
    from app.infrastructure.db import get_async_sessionmaker

    container = get_container()
    session_factory = container.session_factory or get_async_sessionmaker()
    container.session_factory = session_factory
    if container.security_event_service is None:
        container.security_event_service = SecurityEventService(session_factory)
    return container.security_event_service


__all__ = ["SecurityEventService", "get_security_event_service"]
