"""Unit tests for scope normalization and enforcement helpers."""

import pytest
from fastapi import HTTPException

from app.api.dependencies.auth import ScopeSet, require_scopes


def _user(payload_scope: str | None = None, payload_scopes: list[str] | None = None):
    payload: dict[str, object] = {}
    if payload_scope is not None:
        payload["scope"] = payload_scope
    if payload_scopes is not None:
        payload["scopes"] = payload_scopes
    return {
        "user_id": "tester",
        "payload": payload,
    }


def test_scopeset_allows_exact_and_split_scopes() -> None:
    scope_set = ScopeSet(["conversations:read", "conversations:write"])
    assert scope_set.allows("conversations:read")
    assert scope_set.allows("conversations:write")
    assert not scope_set.allows("tools:read")


def test_scopeset_support_superuser_matches_all() -> None:
    scope_set = ScopeSet(["support:*"])
    assert scope_set.allows("conversations:delete")
    assert scope_set.allows("tools:read")


def test_scope_dependency_accepts_multiple_claim_shapes() -> None:
    dependency = require_scopes("conversations:write")
    user_dict = _user(payload_scopes=["conversations:write"])
    assert dependency(user_dict) is user_dict


def test_scope_dependency_raises_for_missing_scope() -> None:
    dependency = require_scopes("conversations:write")
    with pytest.raises(HTTPException) as exc:
        dependency(_user(payload_scope="conversations:read"))
    assert exc.value.status_code == 403
