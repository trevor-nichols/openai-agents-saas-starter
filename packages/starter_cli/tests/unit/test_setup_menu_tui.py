from __future__ import annotations

import argparse

from starter_cli.core.context import build_context
from starter_cli.commands import setup as setup_command
from starter_cli import ui as ui_module


def test_setup_menu_uses_textual(monkeypatch):
    ctx = build_context()
    calls: dict[str, object] = {}

    class DummyTUI:
        def __init__(self, ctx, initial_screen="home") -> None:
            calls["ctx"] = ctx
            calls["initial"] = initial_screen

        def run(self) -> None:
            calls["ran"] = True

    monkeypatch.setattr(ui_module, "StarterTUI", DummyTUI)

    args = argparse.Namespace(no_tui=False, json=False)
    setup_command.handle_setup_menu(args, ctx)

    assert calls.get("ran") is True
    assert calls["initial"] == "setup"
