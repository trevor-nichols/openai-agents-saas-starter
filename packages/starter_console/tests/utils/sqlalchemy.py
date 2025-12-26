"""Shared SQLAlchemy helpers for console test fixtures."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Table
from sqlalchemy.engine import Connection


def create_tables(connection: Connection, tables: Sequence[Table]) -> None:
    """Create each table idempotently for SQLite-backed tests."""

    for table in tables:
        table.create(connection, checkfirst=True)
