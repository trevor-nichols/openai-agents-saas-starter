from __future__ import annotations

import argparse
import sys

import pytest

from starter_cli.core.context import build_context
from starter_cli.commands import setup as setup_command
from starter_cli import ui as ui_module


def test_setup_menu_uses_textual(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = build_context()
    calls: dict[str, object] = {}

    class DummyTUI:
        def __init__(self, ctx, initial_screen="home") -> None:
            calls["ctx"] = ctx
            calls["initial"] = initial_screen

        def run(self) -> None:
            calls["ran"] = True

    monkeypatch.setattr(ui_module, "StarterTUI", DummyTUI)
    monkeypatch.setitem(sys.modules, "starter_cli.ui", ui_module)

    args = argparse.Namespace(no_tui=False, json=False)
    setup_command.handle_setup_menu(args, ctx)

    assert calls.get("ran") is True
    assert calls["initial"] == "setup"
