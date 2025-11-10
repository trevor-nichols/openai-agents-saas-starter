"""Validation for the repo-root CLI package."""

from __future__ import annotations

import importlib
import os
import sys
from collections.abc import Generator
from pathlib import Path

import pytest
from app.core import config as config_module


@pytest.fixture()
def env_snapshot() -> Generator[None, None, None]:
    snapshot = dict(os.environ)
    try:
        yield
    finally:
        current_keys = set(os.environ.keys())
        for key in current_keys - snapshot.keys():
            os.environ.pop(key, None)
        for key, value in snapshot.items():
            os.environ[key] = value


class _FailingSettings:
    def __call__(self, *args, **kwargs):
        raise AssertionError("get_settings should not run at import time for CLI modules.")

    def cache_clear(self):
        return None


def test_cli_imports_do_not_pull_settings(monkeypatch: pytest.MonkeyPatch, env_snapshot) -> None:
    monkeypatch.setattr(config_module, "get_settings", _FailingSettings())

    for name in [m for m in list(sys.modules.keys()) if m.startswith("anything_agents.cli")]:
        del sys.modules[name]

    importlib.import_module("anything_agents.cli.main")


def test_cli_context_loads_custom_env(tmp_path: Path, env_snapshot) -> None:
    env_file = tmp_path / ".env.cli"
    env_file.write_text("APP_PUBLIC_URL=https://cli.example\n", encoding="utf-8")

    from anything_agents.cli.common import CLIContext

    ctx = CLIContext(project_root=tmp_path, env_files=(env_file,))
    ctx.load_environment(verbose=False)

    assert os.environ["APP_PUBLIC_URL"] == "https://cli.example"
