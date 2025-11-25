"""Alembic environment configuration with async engine support."""

from __future__ import annotations

import asyncio
import importlib
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"

for path in (SRC_DIR, BASE_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.core.config import get_settings  # noqa: E402
from app.infrastructure.persistence.models.base import Base  # noqa: E402

# Ensure all ORM metadata is registered before Alembic inspects Base metadata.
importlib.import_module("app.infrastructure.persistence.auth.models")
importlib.import_module("app.infrastructure.persistence.conversations.models")
importlib.import_module("app.infrastructure.persistence.billing.models")

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_database_url() -> str:
    """Return the SQLAlchemy URL configured for migrations."""

    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError(
            "DATABASE_URL (database_url setting) must be configured to run migrations."
        )
    return settings.database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""

    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using async engine."""

    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def do_run_migrations(connection: Connection) -> None:
    """Configure Alembic context and run migrations within a connection."""

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        render_as_batch=False,
    )

    with context.begin_transaction():
        context.run_migrations()


def main() -> None:
    """Entrypoint invoked by Alembic."""

    if context.is_offline_mode():
        run_migrations_offline()
    else:
        asyncio.run(run_migrations_online())


main()
