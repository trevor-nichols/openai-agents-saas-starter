"""Backwards-compatible settings entrypoint.

The legacy `app.core.config` import path re-exports the modular settings package so
existing imports continue to work while the new structure lives under
`app.core.settings`.
"""
from __future__ import annotations

from app.core.settings import (
    Settings,
    SignupAccessPolicyLiteral,
    enforce_secret_overrides,
    enforce_vault_verification,
    get_settings,
)
from app.core.settings.security import (
    DEFAULT_EMAIL_VERIFICATION_TOKEN_PEPPER,
    DEFAULT_KEY_STORAGE_PATH,
    DEFAULT_PASSWORD_PEPPER,
    DEFAULT_PASSWORD_RESET_TOKEN_PEPPER,
    DEFAULT_REFRESH_TOKEN_PEPPER,
    DEFAULT_SECRET_KEY,
    PLACEHOLDER_PASSWORD_PEPPER,
    PLACEHOLDER_REFRESH_TOKEN_PEPPER,
    PLACEHOLDER_SECRET_KEY,
)

__all__ = [
    "Settings",
    "SignupAccessPolicyLiteral",
    "get_settings",
    "enforce_secret_overrides",
    "enforce_vault_verification",
    "DEFAULT_SECRET_KEY",
    "DEFAULT_PASSWORD_PEPPER",
    "DEFAULT_PASSWORD_RESET_TOKEN_PEPPER",
    "DEFAULT_EMAIL_VERIFICATION_TOKEN_PEPPER",
    "DEFAULT_REFRESH_TOKEN_PEPPER",
    "DEFAULT_KEY_STORAGE_PATH",
    "PLACEHOLDER_SECRET_KEY",
    "PLACEHOLDER_PASSWORD_PEPPER",
    "PLACEHOLDER_REFRESH_TOKEN_PEPPER",
]
