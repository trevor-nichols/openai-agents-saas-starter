"""User notification preference management."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Select, and_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.persistence.auth.models import UserNotificationPreference


class NotificationPreferenceService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def upsert_preference(
        self,
        *,
        user_id: UUID,
        channel: str,
        category: str,
        enabled: bool,
        tenant_id: UUID | None,
    ) -> UserNotificationPreference:
        async with self._session_factory() as session:
            now = datetime.now(UTC)
            insert_fn = self._insert_for_dialect(session)
            stmt = insert_fn(UserNotificationPreference).values(
                id=uuid4(),
                user_id=user_id,
                tenant_id=tenant_id,
                channel=channel,
                category=category,
                enabled=enabled,
                created_at=now,
                updated_at=now,
            )
            update_values = {"enabled": stmt.excluded.enabled, "updated_at": now}
            if tenant_id is None:
                stmt = stmt.on_conflict_do_update(
                    index_elements=[
                        UserNotificationPreference.user_id,
                        UserNotificationPreference.channel,
                        UserNotificationPreference.category,
                    ],
                    index_where=UserNotificationPreference.tenant_id.is_(None),
                    set_=update_values,
                )
            else:
                stmt = stmt.on_conflict_do_update(
                    index_elements=[
                        UserNotificationPreference.user_id,
                        UserNotificationPreference.tenant_id,
                        UserNotificationPreference.channel,
                        UserNotificationPreference.category,
                    ],
                    set_=update_values,
                )
            await session.execute(stmt)
            await session.commit()

            query = select(UserNotificationPreference).where(
                and_(
                    UserNotificationPreference.user_id == user_id,
                    UserNotificationPreference.tenant_id == tenant_id,
                    UserNotificationPreference.channel == channel,
                    UserNotificationPreference.category == category,
                )
            )
            result = await session.execute(query)
            pref = result.scalar_one()
            return pref

    async def list_preferences(
        self, *, user_id: UUID, tenant_id: UUID | None = None
    ) -> list[UserNotificationPreference]:
        query: Select[tuple[UserNotificationPreference]] = select(UserNotificationPreference).where(
            UserNotificationPreference.user_id == user_id
        )
        if tenant_id:
            query = query.where(UserNotificationPreference.tenant_id == tenant_id)
        async with self._session_factory() as session:
            result = await session.execute(query)
            return list(result.scalars().all())

    @staticmethod
    def _insert_for_dialect(session: AsyncSession):  # pragma: no cover - trivial
        dialect = session.bind.dialect.name if session.bind else "postgresql"
        if dialect == "sqlite":
            return sqlite_insert
        return pg_insert


def get_notification_preference_service() -> NotificationPreferenceService:
    from app.bootstrap.container import get_container
    from app.infrastructure.db import get_async_sessionmaker

    container = get_container()
    session_factory = container.session_factory or get_async_sessionmaker()
    container.session_factory = session_factory
    if container.notification_preference_service is None:
        container.notification_preference_service = NotificationPreferenceService(
            session_factory
        )
    return container.notification_preference_service


__all__ = ["NotificationPreferenceService", "get_notification_preference_service"]
