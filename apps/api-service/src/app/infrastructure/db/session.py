"""FastAPI dependencies for database access."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from .engine import get_async_sessionmaker


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields an AsyncSession."""

    sessionmaker = get_async_sessionmaker()
    async with sessionmaker() as session:
        yield session
