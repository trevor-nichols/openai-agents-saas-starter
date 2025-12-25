from __future__ import annotations

import pytest
from starter_cli.core import CLIError
from starter_cli.services.auth.security import build_vault_headers


def test_build_vault_headers_returns_dev_local_for_safe_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("AUTH_CLI_DEV_AUTH_MODE", "demo")
    monkeypatch.delenv("VAULT_VERIFY_ENABLED", raising=False)

    header, extras = build_vault_headers({}, None)

    assert header == "Bearer dev-demo"
    assert extras == {}


def test_build_vault_headers_rejects_dev_local_when_hardened(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("VAULT_VERIFY_ENABLED", "true")
    monkeypatch.setenv("AUTH_CLI_DEV_AUTH_MODE", "demo")

    with pytest.raises(CLIError):
        build_vault_headers({}, None)


def test_build_vault_headers_requires_settings_when_verification_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("VAULT_VERIFY_ENABLED", "true")
    monkeypatch.delenv("AUTH_CLI_DEV_AUTH_MODE", raising=False)

    with pytest.raises(CLIError) as exc:
        build_vault_headers({}, None)

    assert "settings" in str(exc.value)
