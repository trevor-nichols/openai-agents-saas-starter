from __future__ import annotations

import argparse
from pathlib import Path

from typing import cast

import pytest
from starter_console.commands import setup as setup_cmd
from starter_console.core import CLIContext, CLIError


def _build_args(**overrides) -> argparse.Namespace:
    defaults = {
        "profile": "demo",
        "profiles_path": None,
        "output": "summary",
        "answers_file": None,
        "var": None,
        "strict": False,
        "report_only": False,
        "non_interactive": False,
        "no_tui": False,
        "export_answers": None,
        "markdown_summary_path": None,
        "summary_path": None,
        "auto_infra": None,
        "auto_secrets": None,
        "auto_stripe": None,
        "auto_sso": None,
        "auto_migrations": None,
        "auto_redis": None,
        "auto_geoip": None,
        "auto_dev_user": None,
        "auto_demo_token": None,
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

    class DummyWizard:
        def __init__(self, **kwargs):
            created.update(kwargs)
            self.summary_path = kwargs.get("summary_path")
            self.markdown_summary_path = kwargs.get("markdown_summary_path")

        def execute(self) -> None:
            created["executed"] = True

        def render_report(self) -> None:  # pragma: no cover - unused in these tests
            created["rendered"] = True

    monkeypatch.setattr(setup_cmd, "SetupWizard", DummyWizard)
    return created


def test_setup_command_launches_textual_wizard_by_default(
    monkeypatch: pytest.MonkeyPatch, dummy_ctx: CLIContext
) -> None:
    calls: dict[str, object] = {}

    class DummyTUI:
        def __init__(self, ctx, initial_screen="home", wizard_config=None) -> None:
            calls["ctx"] = ctx
            calls["initial"] = initial_screen
            calls["config"] = wizard_config

        def run(self) -> None:
            calls["run"] = True

    import starter_console.ui as ui_module

    monkeypatch.setattr(ui_module, "StarterTUI", DummyTUI)

    args = _build_args()

    exit_code = setup_cmd.handle_setup_wizard(args, dummy_ctx)

    assert exit_code == 0
    assert calls["initial"] == "wizard"
    assert calls.get("run") is True
    from starter_console.ui.panes.wizard import WizardLaunchConfig

    config = cast(WizardLaunchConfig, calls["config"])
    assert config.profile == "demo"


def test_setup_command_rejects_no_tui_interactive(
    dummy_ctx: CLIContext,
) -> None:
    args = _build_args(no_tui=True)

    with pytest.raises(CLIError):
        setup_cmd.handle_setup_wizard(args, dummy_ctx)


def test_setup_command_rejects_export_when_report_only(
    dummy_ctx: CLIContext,
) -> None:
    args = _build_args(report_only=True, export_answers="ops/local.json")

    with pytest.raises(CLIError):
        setup_cmd.handle_setup_wizard(args, dummy_ctx)


def test_setup_command_strict_requires_production_profile(dummy_ctx: CLIContext) -> None:
    args = _build_args(profile="staging", strict=True, var=["FOO=bar"])

    with pytest.raises(CLIError):
        setup_cmd.handle_setup_wizard(args, dummy_ctx)


def test_setup_command_strict_requires_answers(dummy_ctx: CLIContext) -> None:
    args = _build_args(profile="production", strict=True)

    with pytest.raises(CLIError):
        setup_cmd.handle_setup_wizard(args, dummy_ctx)


def test_setup_command_strict_forces_headless(
    monkeypatch: pytest.MonkeyPatch, dummy_ctx: CLIContext
) -> None:
    created = _install_dummies(monkeypatch)

    args = _build_args(profile="production", strict=True, var=["FOO=bar"])

    exit_code = setup_cmd.handle_setup_wizard(args, dummy_ctx)

    assert exit_code == 0
    assert created.get("executed") is True
    assert isinstance(created["input_provider"], setup_cmd.HeadlessInputProvider)


def test_setup_command_passes_export_answers_path(
    monkeypatch: pytest.MonkeyPatch, dummy_ctx: CLIContext
) -> None:
    created = _install_dummies(monkeypatch)

    args = _build_args(export_answers="ops/local.json", non_interactive=True)

    exit_code = setup_cmd.handle_setup_wizard(args, dummy_ctx)

    assert exit_code == 0
    assert created["export_answers_path"] == Path("ops/local.json").expanduser()
