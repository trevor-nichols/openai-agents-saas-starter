from __future__ import annotations

import argparse
import sys

import pytest

from starter_cli.core.context import build_context
from starter_cli.commands import home as home_command
from starter_cli import ui as ui_module


def test_home_command_invokes_textual(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = build_context()
    calls: dict[str, object] = {}

    class DummyApp:
        def __init__(self, ctx, initial_screen="home") -> None:
            calls["ctx"] = ctx
            calls["initial"] = initial_screen

        def run(self) -> None:
            calls["run"] = True

    monkeypatch.setattr(ui_module, "StarterTUI", DummyApp)
    monkeypatch.setitem(sys.modules, "starter_cli.ui", ui_module)

    args = argparse.Namespace(no_tui=False)
    result = home_command._handle_home(args, ctx)

    assert result == 0
    assert calls["initial"] == "home"
    assert calls.get("run") is True
