from __future__ import annotations

from starter_cli.core.context import build_context
from starter_cli.workflows.home import service as home_service
from starter_cli.workflows.home.service import HomeController


def test_home_controller_invokes_textual(monkeypatch):
    ctx = build_context()
    controller = HomeController(ctx)

    calls: dict[str, object] = {}

    class DummyApp:
        def __init__(self, ctx, initial_screen="home") -> None:
            calls["ctx"] = ctx
            calls["initial"] = initial_screen

        def run(self) -> None:
            calls["run"] = True

    monkeypatch.setattr(home_service, "StarterTUI", DummyApp)

    result = controller.run(use_tui=True)

    assert result == 0
    assert calls["initial"] == "home"
    assert calls.get("run") is True
