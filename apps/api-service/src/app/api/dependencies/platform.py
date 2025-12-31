"""Platform operator dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, status

from app.api.dependencies.auth import CurrentUser, require_verified_scopes

_OPERATOR_SCOPES = {"platform:operator", "support:*"}


@dataclass(slots=True)
class OperatorOverride:
    actor_id: str | None
    reason: str


def require_platform_operator():
    """Dependency enforcing platform operator scope."""

    return require_verified_scopes(*_OPERATOR_SCOPES, match="any")


def has_operator_scope(user: CurrentUser) -> bool:
    payload = user.get("payload") if isinstance(user, dict) else None
    if not isinstance(payload, dict):
        return False
    scopes: set[str] = set()
    _consume_scope_claim(payload.get("scope"), scopes)
    _consume_scope_claim(payload.get("scopes"), scopes)
    return any(scope in scopes for scope in _OPERATOR_SCOPES)


def resolve_operator_override(
    *,
    operator_override: str | None,
    operator_reason: str | None,
    current_user: CurrentUser,
) -> OperatorOverride | None:
    if not _is_truthy(operator_override):
        return None
    if not has_operator_scope(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Platform operator scope (support:* or platform:operator) "
                "required for override."
            ),
        )
    reason = operator_reason.strip() if operator_reason else ""
    if not reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Operator-Reason header is required when X-Operator-Override is true.",
        )
    return OperatorOverride(actor_id=_resolve_actor_id(current_user), reason=reason)


def _resolve_actor_id(user: CurrentUser) -> str | None:
    if not isinstance(user, dict):
        return None
    payload_obj = user.get("payload")
    payload = payload_obj if isinstance(payload_obj, dict) else {}
    candidate = user.get("user_id") or user.get("subject") or payload.get("sub")
    return str(candidate) if candidate else None


def _consume_scope_claim(value: Any, scopes: set[str]) -> None:
    if value is None:
        return
    if isinstance(value, str):
        scopes.update(item.strip() for item in value.split() if item.strip())
    elif isinstance(value, list | tuple | set):
        for item in value:
            if isinstance(item, str) and item.strip():
                scopes.add(item.strip())


def _is_truthy(value: str | None) -> bool:
    if value is None:
        return False
    normalized = value.strip().lower()
    return normalized in {"1", "true", "yes", "on"}


__all__ = [
    "CurrentUser",
    "OperatorOverride",
    "has_operator_scope",
    "require_platform_operator",
    "resolve_operator_override",
]
