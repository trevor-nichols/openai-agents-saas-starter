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


async def main() -> int:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL must be set for migration checks.", file=sys.stderr)
        return 1

    engine = create_async_engine(database_url, pool_pre_ping=True)
    try:
        versions = await _fetch_versions(engine)
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
