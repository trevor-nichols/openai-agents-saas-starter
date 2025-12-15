"""Shared SQLAlchemy declarative base and helpers."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Integer, MetaData
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(AsyncAttrs, DeclarativeBase):
    """Declarative base with naming conventions shared across modules."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


UTC_NOW = datetime.utcnow


def uuid_pk() -> uuid.UUID:
    """Factory for UUID primary keys."""

    return uuid.uuid4()


# SQLite only auto-increments on INTEGER PRIMARY KEY; BigInteger breaks insert tests.
INT_PK_TYPE = BigInteger().with_variant(Integer, "sqlite")


__all__ = ["Base", "NAMING_CONVENTION", "UTC_NOW", "INT_PK_TYPE", "uuid_pk"]
