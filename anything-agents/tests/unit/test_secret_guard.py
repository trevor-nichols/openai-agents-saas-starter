"""Tests for secret guard rails."""

from __future__ import annotations

import pytest

from app.core.config import (
    DEFAULT_PASSWORD_PEPPER,
    DEFAULT_REFRESH_TOKEN_PEPPER,
    DEFAULT_SECRET_KEY,
    PLACEHOLDER_PASSWORD_PEPPER,
    PLACEHOLDER_REFRESH_TOKEN_PEPPER,
    PLACEHOLDER_SECRET_KEY,
    Settings,
    enforce_secret_overrides,
)


def test_secret_warnings_detect_defaults() -> None:
    settings = Settings.model_validate(
        {
            "secret_key": DEFAULT_SECRET_KEY,
            "AUTH_PASSWORD_PEPPER": DEFAULT_PASSWORD_PEPPER,
            "AUTH_REFRESH_TOKEN_PEPPER": DEFAULT_REFRESH_TOKEN_PEPPER,
        }
    )
    warnings = settings.secret_warnings()
    assert any("SECRET_KEY" in warning for warning in warnings)


def test_secret_warnings_detect_placeholders() -> None:
    settings = Settings.model_validate(
        {
            "secret_key": PLACEHOLDER_SECRET_KEY,
            "AUTH_PASSWORD_PEPPER": PLACEHOLDER_PASSWORD_PEPPER,
            "AUTH_REFRESH_TOKEN_PEPPER": PLACEHOLDER_REFRESH_TOKEN_PEPPER,
        }
    )
    warnings = settings.secret_warnings()
    assert any("SECRET_KEY" in warning for warning in warnings)
    assert any("AUTH_PASSWORD_PEPPER" in warning for warning in warnings)
    assert any("AUTH_REFRESH_TOKEN_PEPPER" in warning for warning in warnings)


def test_enforce_secret_overrides_in_production() -> None:
    settings = Settings(
        debug=False,
        environment="production",
        secret_key=DEFAULT_SECRET_KEY,
        auth_password_pepper=DEFAULT_PASSWORD_PEPPER,
        auth_refresh_token_pepper=DEFAULT_REFRESH_TOKEN_PEPPER,
    )
    with pytest.raises(RuntimeError):
        enforce_secret_overrides(settings, force=True)


def test_dev_mode_allows_defaults() -> None:
    settings = Settings(debug=True)
    enforce_secret_overrides(settings)
