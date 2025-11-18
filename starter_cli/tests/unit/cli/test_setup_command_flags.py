from __future__ import annotations

import argparse
from pathlib import Path

import pytest
from starter_cli.commands import setup as setup_cmd
from starter_cli.core import CLIContext


def _build_args(**overrides) -> argparse.Namespace:
    defaults = {
        "profile": "local",
        "output": "summary",
        "answers_file": None,
        "var": None,
        "report_only": False,
        "non_interactive": False,
        "legacy_flow": False,
        "no_tui": False,
        "no_schema": False,
        "markdown_summary_path": None,
        "summary_path": None,
        "auto_infra": None,
        "auto_secrets": None,
        "auto_stripe": None,
        "auto_migrations": None,
        "auto_redis": None,
        "auto_geoip": None,
        # flags that map to argparse choices but default via Namespace
        "setup_command": "wizard",
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


@pytest.fixture(name="dummy_ctx")
def _dummy_ctx(tmp_path: Path) -> CLIContext:
    return CLIContext(project_root=tmp_path, env_files=())


def _install_dummies(monkeypatch: pytest.MonkeyPatch):
    created: dict[str, object] = {}

    class DummyInteractive:
        def __init__(self, prefill: dict[str, str]):
            self.prefill = prefill

    class DummyWizard:
        def __init__(self, **kwargs):
            created.update(kwargs)
            self.summary_path = kwargs.get("summary_path")
            self.markdown_summary_path = kwargs.get("markdown_summary_path")

        def execute(self) -> None:
            created["executed"] = True

        def render_report(self) -> None:  # pragma: no cover - unused in these tests
            created["rendered"] = True

    monkeypatch.setattr(setup_cmd, "InteractiveInputProvider", DummyInteractive)
    monkeypatch.setattr(setup_cmd, "SetupWizard", DummyWizard)
    return created


def test_setup_command_enables_shell_and_tui_by_default(
    monkeypatch: pytest.MonkeyPatch, dummy_ctx: CLIContext
) -> None:
    created = _install_dummies(monkeypatch)

    args = _build_args()

    exit_code = setup_cmd.handle_setup_wizard(args, dummy_ctx)

    assert exit_code == 0
    assert created["enable_shell"] is True
    assert created["enable_tui"] is True
    assert created.get("executed") is True


def test_setup_command_disables_shell_and_tui_when_requested(
    monkeypatch: pytest.MonkeyPatch, dummy_ctx: CLIContext
) -> None:
    created = _install_dummies(monkeypatch)

    args = _build_args(no_tui=True)

    exit_code = setup_cmd.handle_setup_wizard(args, dummy_ctx)

    assert exit_code == 0
    assert created["enable_shell"] is False
    assert created["enable_tui"] is False
