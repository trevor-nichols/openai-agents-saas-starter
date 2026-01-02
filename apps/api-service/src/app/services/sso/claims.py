"""OIDC claim normalization helpers for SSO."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

from app.core.normalization import normalize_email
from app.domain.users import UserProfilePatch

from .errors import SsoTokenError


def require_claim(claims: Mapping[str, Any], key: str) -> str:
    value = claims.get(key)
    if not isinstance(value, str) or not value:
        raise SsoTokenError(
            f"OIDC token missing required claim: {key}.",
            reason=f"missing_claim:{key}",
        )
    return value


def optional_str_claim(claims: Mapping[str, Any], key: str) -> str | None:
    value = claims.get(key)
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return None


def parse_bool_claim(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    if isinstance(value, int):
        return value != 0
    return False


def profile_patch_from_claims(
    claims: Mapping[str, Any],
) -> tuple[UserProfilePatch, set[str]]:
    update = UserProfilePatch(
        display_name=optional_str_claim(claims, "name"),
        given_name=optional_str_claim(claims, "given_name"),
        family_name=optional_str_claim(claims, "family_name"),
        avatar_url=optional_str_claim(claims, "picture"),
        locale=optional_str_claim(claims, "locale"),
    )
    provided_fields = {
        field for field, value in asdict(update).items() if value is not None
    }
    return update, provided_fields


def identity_profile_from_claims(claims: Mapping[str, Any]) -> dict[str, Any]:
    profile: dict[str, Any] = {}
    for key in ("name", "given_name", "family_name", "picture", "locale", "hd"):
        value = claims.get(key)
        if value is not None:
            profile[key] = value
    return profile


__all__ = [
    "identity_profile_from_claims",
    "normalize_email",
    "optional_str_claim",
    "parse_bool_claim",
    "profile_patch_from_claims",
    "require_claim",
]
