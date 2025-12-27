from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Callable, Sequence
from typing import Any

from app.api.dependencies.auth import require_current_user

from tests.utils.contract_env import DEFAULT_SCOPE, TEST_TENANT_ID


_UNSET = object()


def make_user_payload(
    *,
    scope: str | None = None,
    tenant_id: str | None | object = _UNSET,
    roles: Sequence[str] = ("admin",),
    user_id: str = "test-user",
) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "subject": f"user:{user_id}",
        "payload": {
            "scope": scope or DEFAULT_SCOPE,
            "tenant_id": TEST_TENANT_ID if tenant_id is _UNSET else tenant_id,
            "roles": list(roles),
        },
    }


@contextmanager
def override_current_user(app, factory: Callable[[], dict[str, Any]]):
    """Temporarily override the auth dependency for a test module."""

    previous = app.dependency_overrides.get(require_current_user)
    app.dependency_overrides[require_current_user] = factory
    try:
        yield
    finally:
        if previous is None:
            app.dependency_overrides.pop(require_current_user, None)
        else:
            app.dependency_overrides[require_current_user] = previous
