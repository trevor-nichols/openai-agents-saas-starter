from __future__ import annotations

import argparse
from typing import cast
from pathlib import Path

import pytest
from starter_console.commands import sso as sso_command
from starter_console.core import CLIContext, CLIError
from starter_console.services.sso import SsoProviderSeedConfig, SsoSetupResult


def _build_args(**overrides) -> argparse.Namespace:
    defaults = {
        "preset": None,
        "provider": "google",
        "scope": None,
        "tenant_id": None,
        "tenant_slug": None,
        "issuer_url": "https://accounts.google.com",
        "discovery_url": None,
        "client_id": "client-id",
        "client_secret": "client-secret",
        "scopes": None,
        "token_auth_method": None,
        "id_token_algs": None,
        "allowed_domains": None,
        "auto_provision_policy": None,
        "default_role": None,
        "enabled": None,
        "pkce_required": None,
        "from_env": False,
        "non_interactive": True,
        "list_presets": False,
        "sso_command": "setup",
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def test_sso_setup_command_builds_config(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ctx = CLIContext(project_root=tmp_path, env_files=())
    args = _build_args()
    captured: dict[str, object] = {}

    def fake_run(ctx_arg: CLIContext, *, config, update_env: bool):
        captured["ctx"] = ctx_arg
        captured["config"] = config
        captured["update_env"] = update_env
        return SsoSetupResult(
            result="created",
            provider_key=config.provider_key,
            tenant_id=None,
            tenant_slug=None,
            config_id="config-id",
        )

    monkeypatch.setattr(sso_command, "run_sso_setup", fake_run)
    monkeypatch.setattr(sso_command, "load_env_values", lambda _: {})

    exit_code = sso_command.handle_sso_setup(args, ctx)

    assert exit_code == 0
    assert captured["update_env"] is True
    config = cast(SsoProviderSeedConfig, captured["config"])
    assert config.provider_key == "google"
    assert config.client_id == "client-id"
    assert config.client_secret == "client-secret"
    assert config.auto_provision_policy == "invite_only"
    assert config.token_auth_method == "client_secret_post"
    assert config.allowed_id_token_algs == []


def test_sso_setup_lists_presets(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ctx = CLIContext(project_root=tmp_path, env_files=())
    args = _build_args(list_presets=True, provider=None)
    called = {"run": False}

    def fake_run(*_args, **_kwargs):
        called["run"] = True
        return None

    monkeypatch.setattr(sso_command, "run_sso_setup", fake_run)

    exit_code = sso_command.handle_sso_setup(args, ctx)

    assert exit_code == 0
    assert called["run"] is False


def test_sso_setup_unknown_provider_requires_issuer(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ctx = CLIContext(project_root=tmp_path, env_files=())
    args = _build_args(provider="acme", issuer_url=None, discovery_url=None)

    monkeypatch.setattr(sso_command, "load_env_values", lambda _: {})

    with pytest.raises(CLIError, match="OIDC issuer URL is required"):
        sso_command.handle_sso_setup(args, ctx)
