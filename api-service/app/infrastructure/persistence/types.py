"""Cross-dialect column types used by ORM models."""

from __future__ import annotations

from typing import Any

from sqlalchemy.engine import Dialect
from sqlalchemy.types import JSON, String, TypeDecorator


class CITEXTCompat(TypeDecorator[str]):
    """CITEXT-compatible type that degrades to VARCHAR on non-Postgres backends."""

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import CITEXT

            return dialect.type_descriptor(CITEXT())
        # SQLite/MySQL fallback: case-sensitive string; callers enforce lower/unique in app layer.
        return dialect.type_descriptor(String(255))


class JSONBCompat(TypeDecorator[Any]):
    """JSON type that prefers JSONB on Postgres but works elsewhere."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> Any:
        if dialect.name == "postgresql":
            from sqlalchemy import Text
            from sqlalchemy.dialects.postgresql import JSONB

            return dialect.type_descriptor(JSONB(astext_type=Text()))
        return dialect.type_descriptor(JSON())


__all__ = ["CITEXTCompat", "JSONBCompat"]
