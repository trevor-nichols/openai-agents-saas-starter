"""Consent capture and retrieval for users."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Select, desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.persistence.auth.models import UserConsent


class ConsentService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def record(
        self,
        *,
        user_id: UUID,
        policy_key: str,
        version: str,
        ip_hash: str | None = None,
        user_agent_hash: str | None = None,
    ) -> UserConsent:
        async with self._session_factory() as session:
            consent = UserConsent(
                id=uuid4(),
                user_id=user_id,
                policy_key=policy_key,
                version=version,
                accepted_at=datetime.now(UTC),
                ip_hash=ip_hash,
                user_agent_hash=user_agent_hash,
                created_at=datetime.now(UTC),
            )
            session.add(consent)
            try:
                await session.commit()
                await session.refresh(consent)
                return consent
            except IntegrityError:
                await session.rollback()
                # Fetch existing consent to keep idempotent behavior
                query = select(UserConsent).where(
                    UserConsent.user_id == user_id,
                    UserConsent.policy_key == policy_key,
                    UserConsent.version == version,
                )
                result = await session.execute(query)
                existing = result.scalar_one()
                return existing

    async def list_for_user(self, *, user_id: UUID, limit: int = 50) -> list[UserConsent]:
        query: Select[tuple[UserConsent]] = (
            select(UserConsent)
            .where(UserConsent.user_id == user_id)
            .order_by(desc(UserConsent.accepted_at))
            .limit(limit)
        )
        async with self._session_factory() as session:
            result = await session.execute(query)
            return list(result.scalars().all())


def get_consent_service() -> ConsentService:
    from app.bootstrap.container import get_container
    from app.infrastructure.db import get_async_sessionmaker

    container = get_container()
    session_factory = container.session_factory or get_async_sessionmaker()
    container.session_factory = session_factory
    if container.consent_service is None:
        container.consent_service = ConsentService(session_factory)
    return container.consent_service


__all__ = ["ConsentService", "get_consent_service"]
