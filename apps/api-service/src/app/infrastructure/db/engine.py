"""Async SQLAlchemy engine and session factory management."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

logger = logging.getLogger("api-service.db")

_engine_lock = asyncio.Lock()
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine | None:
    """Return the shared async engine instance, if initialised."""

    return _engine


def get_async_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Return the global async session factory."""

    if _session_factory is None:
        raise RuntimeError(
            "Database session factory has not been initialised. "
            "Call init_engine() during application startup."
        )
    return _session_factory


async def init_engine(*, run_migrations: bool = False) -> AsyncEngine | None:
    """Initialise the async engine based on application settings."""

    settings = get_settings()

    database_url = settings.database_url
    if not database_url:
        raise RuntimeError(
            "Durable storage is enabled but no database_url is configured. "
            "Set DATABASE_URL or disable durable persistence."
        )

    global _engine, _session_factory

    if _engine is not None:
        return _engine

    async with _engine_lock:
        if _engine is None:
            engine_kwargs: dict[str, object] = {
                "echo": settings.database_echo,
            }
            if database_url.startswith("sqlite+"):
                engine_kwargs["poolclass"] = NullPool
            else:
                engine_kwargs.update(
                    pool_size=settings.database_pool_size,
                    max_overflow=settings.database_max_overflow,
                    pool_recycle=settings.database_pool_recycle,
                    pool_timeout=settings.database_pool_timeout,
                )

            logger.info(
                "Initialising async engine (url=%s)",
                database_url,
            )
            _engine = create_async_engine(
                database_url,
                **engine_kwargs,
            )
            _session_factory = async_sessionmaker(
                _engine,
                expire_on_commit=False,
                autoflush=False,
            )

            if run_migrations:
                await run_migrations_if_configured(force=True)

            await verify_database_connection()

    return _engine


async def dispose_engine() -> None:
    """Dispose of the shared async engine and reset the session factory."""

    global _engine, _session_factory
    async with _engine_lock:
        if _engine is not None:
            await _engine.dispose()
        _engine = None
        _session_factory = None


async def verify_database_connection(timeout: float | None = None) -> None:
    """Execute a lightweight query to ensure the database is reachable."""

    if _engine is None:
        logger.debug("No engine initialised; skipping database verification.")
        return

    timeout = timeout or get_settings().database_health_timeout
    logger.debug("Verifying database connectivity (timeout=%s)", timeout)

    async with asyncio.timeout(timeout):
        async with _engine.connect() as connection:
            await connection.execute(text("SELECT 1"))


async def run_migrations_if_configured(*, force: bool = False) -> None:
    """Run Alembic migrations when auto-run is enabled in settings."""

    settings = get_settings()
    if not settings.auto_run_migrations and not force:
        logger.debug("Auto-run migrations disabled; skipping.")
        return

    database_url = settings.database_url
    if not database_url:
        raise RuntimeError("auto_run_migrations is enabled but DATABASE_URL is not configured.")

    url = make_url(database_url)
    if url.get_backend_name().startswith("sqlite"):
        logger.info(
            "auto_run_migrations enabled for SQLite; applying SQLAlchemy metadata "
            "instead of Alembic migrations (tests/dev convenience)."
        )
        await _create_sqlite_schema()
        return

    try:
        from alembic import command
        from alembic.config import Config
    except ModuleNotFoundError as exc:  # pragma: no cover - dev configuration issue
        logger.warning("auto_run_migrations is enabled but Alembic is not installed: %s", exc)
        return

    alembic_cfg = Config(str(_resolve_alembic_ini()))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    alembic_cfg.set_main_option("script_location", str(_resolve_alembic_scripts()))

    logger.info("Running Alembic migrations (database_url=%s)", database_url)
    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")


def _resolve_alembic_ini() -> Path:
    """Return the absolute path to the Alembic configuration file."""

    project_root = Path(__file__).resolve().parents[3]
    return project_root / "alembic.ini"


def _resolve_alembic_scripts() -> Path:
    """Return the absolute path to the Alembic migrations directory."""

    project_root = Path(__file__).resolve().parents[3]
    return project_root / "alembic"


async def _create_sqlite_schema() -> None:
    """Populate an in-memory SQLite database using SQLAlchemy metadata.

    Alembic migrations target Postgres and rely on extensions such as CITEXT,
    which are unavailable in SQLite. For test environments that set
    DATABASE_URL=sqlite+aiosqlite:///:memory: and enable auto_run_migrations,
    fall back to creating tables directly from the ORM models.
    """

    if _engine is None:
        raise RuntimeError("Engine must be initialised before bootstrapping SQLite schema.")

    _import_all_models()

    async with _engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: _create_all_tables(sync_conn))


def _create_all_tables(connection) -> None:
    from app.infrastructure.persistence.models.base import Base

    Base.metadata.create_all(bind=connection)


def _import_all_models() -> None:
    """Import all ORM models so they register with the Base metadata."""

    # ruff: noqa: I001 - keep grouped first-party imports together inside function
    # Register ORM models so Base.metadata is populated (SQLite auto-migrate path).
    from app.infrastructure.persistence.auth import models as _auth_models  # noqa: F401
    from app.infrastructure.persistence.billing import models as _billing_models  # noqa: F401
    from app.infrastructure.persistence.conversations import models as _conversation_models  # noqa: F401
    from app.infrastructure.persistence.status import models as _status_models  # noqa: F401
    from app.infrastructure.persistence.stripe import models as _stripe_models  # noqa: F401
    from app.infrastructure.persistence.tenants import models as _tenant_models  # noqa: F401
    from app.infrastructure.persistence.vector_stores import models as _vector_store_models  # noqa: F401
    from app.infrastructure.persistence.workflows import models as _workflow_models  # noqa: F401


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Async context manager that yields a session and handles commit/rollback."""

    sessionmaker = get_async_sessionmaker()
    async with sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
