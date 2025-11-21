from __future__ import annotations

import starter_cli.workflows.setup_menu.controller as controller_module
from starter_cli.core.context import build_context
from starter_cli.workflows.setup_menu.controller import SetupMenuController


def test_setup_menu_uses_textual(monkeypatch):
    ctx = build_context()
    calls: dict[str, object] = {}

    class DummyTUI:
        def __init__(self, ctx, initial_screen="home") -> None:
            calls["ctx"] = ctx
            calls["initial"] = initial_screen

        def run(self) -> None:
            calls["ran"] = True

    monkeypatch.setattr(controller_module, "StarterTUI", DummyTUI)

    controller = SetupMenuController(ctx)
    controller.run(use_tui=True, output_json=False)

    assert calls.get("ran") is True
    assert calls["initial"] == "setup"
