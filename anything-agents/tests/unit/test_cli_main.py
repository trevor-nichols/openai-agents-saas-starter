"""Regression tests for the CLI entrypoint."""

from __future__ import annotations

import pytest
from anything_agents.cli import main as cli_main
from starter_shared import config as shared_config


class _FailingSettings:
    def __call__(self, *args, **kwargs):  # pragma: no cover - triggered by regression only
        raise AssertionError("get_settings should not run when showing help")

    def cache_clear(self) -> None:
        return None


def test_cli_help_does_not_touch_settings(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    """`python -m anything_agents.cli` without subcommands should not load settings."""

    monkeypatch.setattr(shared_config, "get_settings", _FailingSettings())

    exit_code = cli_main.main(["--skip-env"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "usage:" in captured.out.lower()
