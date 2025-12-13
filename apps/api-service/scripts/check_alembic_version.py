"""Fail fast if alembic_version contains multiple rows.

Intended to guard against manual stamps or direct inserts that leave
diverged heads recorded in the database. Safe to run against a fresh
database before the alembic_version table exists.
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Sequence
from urllib.parse import unquote, urlparse

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.exc import ProgrammingError


async def _fetch_versions(engine: AsyncEngine) -> Sequence[str]:
    async with engine.connect() as conn:
        try:
            result = await conn.execute(text("select version_num from alembic_version"))
        except ProgrammingError:
            # Table does not exist yet on a fresh database.
            return []
        return [row[0] for row in result.fetchall()]


def _describe_database_url(database_url: str) -> dict[str, str]:
    parsed = urlparse(database_url)
    return {
        "scheme": parsed.scheme,
        "username": unquote(parsed.username or ""),
        "host": parsed.hostname or "",
        "port": str(parsed.port or ""),
        "database": unquote((parsed.path or "").lstrip("/")),
    }


def _sanitize_database_url(database_url: str) -> str:
    parts = _describe_database_url(database_url)
    scheme = parts["scheme"] or "postgresql"
    user = parts["username"]
    host = parts["host"]
    port = parts["port"]
    database = parts["database"]

    auth = f"{user}@" if user else ""
    host_part = host
    if port:
        host_part = f"{host}:{port}"
    if database:
        return f"{scheme}://{auth}{host_part}/{database}"
    return f"{scheme}://{auth}{host_part}"


def _connection_error_hint(database_url: str, exc: BaseException) -> str:
    parts = _describe_database_url(database_url)
    expected_db = (os.environ.get("POSTGRES_DB") or "").strip()
    actual_db = parts.get("database") or ""

    exc_name = exc.__class__.__name__
    message = str(exc)
    missing_db = exc_name == "InvalidCatalogNameError" or "does not exist" in message.lower()
    if missing_db and expected_db and actual_db and expected_db != actual_db:
        return (
            f"POSTGRES_DB is set to {expected_db!r}, but DATABASE_URL points to {actual_db!r}. "
            "Update DATABASE_URL (or rerun the setup wizard) so they match, then restart the "
            "compose stack if needed."
        )

    if missing_db:
        return (
            "The database referenced by DATABASE_URL does not exist. For local Docker Postgres, "
            "ensure POSTGRES_DB matches the database name in DATABASE_URL, then restart the "
            "compose stack."
        )

    return (
        "Could not connect to the database. Verify DATABASE_URL is reachable and that the local "
        "compose stack is running (`just dev-up`)."
    )


async def main() -> int:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL must be set for migration checks.", file=sys.stderr)
        return 1

    engine = create_async_engine(database_url, pool_pre_ping=True)
    try:
        try:
            versions = await _fetch_versions(engine)
        except Exception as exc:  # noqa: BLE001 - tooling error path
            safe_url = _sanitize_database_url(database_url)
            hint = _connection_error_hint(database_url, exc)
            print(
                "Failed to connect to the database while checking Alembic state.\n"
                f"- DATABASE_URL: {safe_url}\n"
                f"- Hint: {hint}",
                file=sys.stderr,
            )
            return 1
    finally:
        await engine.dispose()

    if len(versions) <= 1:
        return 0

    print(
        f"Detected multiple rows in alembic_version: {versions}. "
        "Clean the table or recreate the database before running migrations.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
