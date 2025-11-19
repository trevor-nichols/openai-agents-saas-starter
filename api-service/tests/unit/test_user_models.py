"""Unit tests covering ORM metadata for user tables."""

from __future__ import annotations

from typing import cast

from sqlalchemy import Enum as SAEnum
from sqlalchemy.inspection import inspect

from app.infrastructure.persistence.auth.models import (
    TenantUserMembership,
    UserAccount,
    UserLoginEvent,
)


def test_user_account_schema_contains_expected_columns() -> None:
    mapper = inspect(UserAccount)
    column_names = {column.key for column in mapper.columns}
    assert {
        "id",
        "email",
        "password_hash",
        "password_pepper_version",
        "status",
        "created_at",
        "updated_at",
    }.issubset(column_names)

    status_col = mapper.columns["status"]
    assert isinstance(status_col.type, SAEnum)
    enum_type = cast(SAEnum, status_col.type)
    assert enum_type.enums is not None
    assert set(enum_type.enums) == {"pending", "active", "disabled", "locked"}


def test_membership_and_login_relationships_configured() -> None:
    membership_mapper = inspect(TenantUserMembership)
    rel_names = set(membership_mapper.relationships.keys())
    assert {"user", "tenant"}.issubset(rel_names)

    login_mapper = inspect(UserLoginEvent)
    rel_names = set(login_mapper.relationships.keys())
    assert "user" in rel_names
