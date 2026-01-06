from __future__ import annotations

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Static

from starter_console.core import CLIContext
from starter_console.core.constants import DEFAULT_ENV_FILES
from starter_console.ui.panes.context import ContextPane


class ContextPanelApp(App[None]):
    def __init__(self, ctx: CLIContext) -> None:
        super().__init__()
        self._ctx = ctx

    def compose(self) -> ComposeResult:
        yield ContextPane(self._ctx)


@pytest.mark.asyncio
async def test_context_panel_summary_shows_profile(tmp_path, monkeypatch) -> None:
    ctx = CLIContext(project_root=tmp_path)
    ctx.env_files = (tmp_path / ".env.local", tmp_path / ".env")
    ctx.loaded_env_files = [tmp_path / ".env.local"]

    class _Settings:
        environment = "staging"

    monkeypatch.setattr(CLIContext, "optional_settings", lambda self: _Settings())

    app = ContextPanelApp(ctx)
    async with app.run_test() as pilot:
        await pilot.pause()
        summary = app.query_one("#context-summary", Static)
        text = str(summary.renderable)
        assert "Env: staging (settings)" in text
        total = len(DEFAULT_ENV_FILES) + 2
        assert f"files: {total} (loaded 1)" in text
        assert "skip defaults: no" in text


@pytest.mark.asyncio
async def test_context_panel_blocks_default_env_add(tmp_path) -> None:
    ctx = CLIContext(project_root=tmp_path)
    app = ContextPanelApp(ctx)
    default_path = DEFAULT_ENV_FILES[0]

    async with app.run_test() as pilot:
        panel = app.query_one(ContextPane)
        ok, status = panel._state.add_custom(str(default_path))
        await pilot.pause()

        assert not ok
        assert "Defaults are managed by Skip env load" in status
        assert panel._state.custom_env_files == []
