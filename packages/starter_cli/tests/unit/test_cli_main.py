"""Regression tests for the CLI entrypoint."""

from __future__ import annotations

import pytest
from starter_cli import app as cli_app
from starter_contracts import config as shared_config


class _FailingSettings:
    def __call__(self, *args, **kwargs):  # pragma: no cover - triggered by regression only
        raise AssertionError("get_settings should not run when showing help")

    def cache_clear(self) -> None:
        return None


def test_cli_default_launch_does_not_touch_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """`python -m starter_cli.app` without subcommands should not load settings."""

    monkeypatch.setattr(shared_config, "get_settings", _FailingSettings())

    calls: dict[str, object] = {}

    def _fake_launch_tui(ctx, *, initial_screen: str) -> int:
        calls["ctx"] = ctx
        calls["initial"] = initial_screen
        return 0

    monkeypatch.setattr(cli_app, "_launch_tui", _fake_launch_tui)

    exit_code = cli_app.main(["--skip-env"])

    assert exit_code == 0
    assert calls["initial"] == "home"
