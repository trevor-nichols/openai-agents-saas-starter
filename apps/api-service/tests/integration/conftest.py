"""Shared fixtures for integration test suite."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator, Iterator

import asyncpg
import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from alembic import command
from alembic.config import Config

from .test_postgres_migrations import (
    ALEMBIC_INI,
    _require_database_url,
)


@pytest.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    """Session-scoped event loop required by async pg fixtures."""

    loop = asyncio.new_event_loop()
    # Mark as original to avoid pytest-asyncio source-inspection failure when files move.
    loop.__original_fixture_loop = True  # type: ignore[attr-defined]
    try:
        yield loop
    finally:
        loop.close()


@pytest.fixture(scope="session")
async def postgres_database(event_loop: asyncio.AbstractEventLoop) -> AsyncIterator[str]:
    """Provision a temporary Postgres database for integration tests."""

    base_url = _require_database_url()
    temp_db_name = f"agents_ci_{uuid.uuid4().hex[:8]}"
    admin_url = base_url.set(drivername="postgresql", database="postgres")

    conn = await asyncpg.connect(str(admin_url))
    try:
        await conn.execute(f'CREATE DATABASE "{temp_db_name}"')
    finally:
        await conn.close()

    test_url = base_url.set(database=temp_db_name)
    try:
        yield test_url.render_as_string(hide_password=False)
    finally:
        admin_conn = await asyncpg.connect(str(admin_url))
        try:
            await admin_conn.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = $1 AND pid <> pg_backend_pid()
                """,
                temp_db_name,
            )
            await admin_conn.execute(f'DROP DATABASE "{temp_db_name}"')
        finally:
            await admin_conn.close()


@pytest.fixture(scope="session")
async def migrated_engine(postgres_database: str) -> AsyncIterator[AsyncEngine]:
    """Apply Alembic migrations against the temporary database and yield an engine."""

    alembic_cfg = Config(str(ALEMBIC_INI))
    alembic_cfg.set_main_option("sqlalchemy.url", postgres_database)

    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")

    engine = create_async_engine(postgres_database, future=True)
    try:
        yield engine
    finally:
        await engine.dispose()
        await asyncio.to_thread(command.downgrade, alembic_cfg, "base")


@pytest.fixture(scope="session")
def migrated_session_factory(migrated_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Session factory bound to the migrated transient Postgres database."""

    return async_sessionmaker(migrated_engine, expire_on_commit=False)


__all__ = [
    "event_loop",
    "postgres_database",
    "migrated_engine",
    "migrated_session_factory",
]
