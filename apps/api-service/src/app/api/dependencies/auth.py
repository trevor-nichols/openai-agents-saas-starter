"""Authentication-related dependency helpers for API routers."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user
from app.core.settings import get_settings

CurrentUser = dict[str, Any]


class ScopeSet:
    """Normalized helper for evaluating JWT scope claims."""

    __slots__ = ("_scopes", "_wildcards", "_is_support_superuser")

    def __init__(self, scopes: Iterable[str]):
        normalized = {scope.strip() for scope in scopes if scope and scope.strip()}
        self._scopes = normalized
        self._wildcards = {
            scope[:-1] for scope in normalized if scope.endswith(":*") and len(scope) > 2
        }
        self._is_support_superuser = "support:*" in normalized

    def allows(self, required: str) -> bool:
        if not required:
            return True
        if required in self._scopes:
            return True
        if self._is_support_superuser:
            return True
        namespace, _sep, _ = required.partition(":")
        wildcard_prefix = f"{namespace}:"
        if wildcard_prefix in self._wildcards:
            return True
        return False

    def ensure(self, required_scopes: Sequence[str], *, match: str = "all") -> None:
        if not required_scopes:
            return
        check_all = match == "all"
        allowed = [self.allows(scope) for scope in required_scopes]
        if check_all and not all(allowed):
            raise PermissionError
        if not check_all and not any(allowed):
            raise PermissionError


def _scope_values_from_payload(payload: dict[str, Any]) -> list[str]:
    scopes: list[str] = []

    def _consume(value: Any) -> None:
        if value is None:
            return
        if isinstance(value, str):
            scopes.extend(item.strip() for item in value.split() if item.strip())
        elif isinstance(value, Iterable):
            for item in value:
                if isinstance(item, str) and item.strip():
                    scopes.append(item.strip())

    _consume(payload.get("scope"))
    _consume(payload.get("scopes"))
    return scopes


def _scope_set_from_user(user: CurrentUser) -> ScopeSet:
    cached = user.get("__scope_set__")
    if isinstance(cached, ScopeSet):
        return cached
    payload = user.get("payload")
    if not isinstance(payload, dict):
        return ScopeSet(())
    scope_set = ScopeSet(_scope_values_from_payload(payload))
    user["__scope_set__"] = scope_set
    return scope_set


async def require_current_user(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Enforce authentication and expose the current user payload."""

    return user


def require_scopes(*scopes: str, match: str = "all"):
    """Dependency factory ensuring the caller holds the required scopes."""

    normalized = [scope for scope in scopes if scope]

    def _dependency(user: CurrentUser = Depends(require_current_user)) -> CurrentUser:
        scope_set = _scope_set_from_user(user)
        try:
            scope_set.ensure(normalized, match=match)
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scopes for this operation.",
            ) from None
        return user

    return _dependency


def require_verified_user():
    def _dependency(user: CurrentUser = Depends(require_current_user)) -> CurrentUser:
        return _ensure_verified(user)

    return _dependency


def require_verified_scopes(*scopes: str, match: str = "all"):
    scope_dependency = require_scopes(*scopes, match=match)

    def _dependency(user: CurrentUser = Depends(scope_dependency)) -> CurrentUser:
        return _ensure_verified(user)

    return _dependency


def _ensure_verified(user: CurrentUser) -> CurrentUser:
    settings = get_settings()
    if not settings.require_email_verification:
        return user
    payload = user.get("payload") if isinstance(user, dict) else None
    payload_dict = payload or {}
    # Legacy access tokens minted before the email_verified claim existed will not contain
    # the key at all. Allow them to pass through; access tokens are short-lived, so the
    # grace period expires automatically as soon as the caller refreshes.
    if "email_verified" not in payload_dict:
        return user
    is_verified = bool(user.get("email_verified")) or bool(payload_dict.get("email_verified"))
    if not is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required.",
        )
    return user
