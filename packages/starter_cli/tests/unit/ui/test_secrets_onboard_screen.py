from __future__ import annotations

from typing import cast

import pytest
from textual.app import App
from textual.widgets import Input, RadioButton, RadioSet, Static

from starter_cli.core import CLIContext
from starter_cli.ui.secrets_onboard import SecretsOnboardScreen


class _TestApp(App[None]):
    def __init__(self, ctx: CLIContext, *, skip_automation: bool = False) -> None:
        self._ctx = ctx
        self._skip_automation = skip_automation
        super().__init__()

    def on_mount(self) -> None:
        self.push_screen(SecretsOnboardScreen(self._ctx, skip_automation=self._skip_automation))


@pytest.mark.asyncio
async def test_secrets_onboard_screen_renders(tmp_path) -> None:
    ctx = CLIContext(project_root=tmp_path)
    async with _TestApp(ctx).run_test() as pilot:
        await pilot.pause()
        screen = pilot.app.screen
        radio_set = screen.query_one("#secrets-providers", RadioSet)
        buttons = list(radio_set.query(RadioButton))
        assert buttons


@pytest.mark.asyncio
async def test_secrets_onboard_start_and_first_prompt(tmp_path) -> None:
    ctx = CLIContext(project_root=tmp_path)
    async with _TestApp(ctx, skip_automation=True).run_test() as pilot:
        await pilot.pause()
        screen = cast(SecretsOnboardScreen, pilot.app.screen)
        await pilot.click("#secrets-start")

        input_field = cast(Input, screen.query_one("#secrets-input"))
        for _ in range(50):
            await pilot.pause(0.1)
            if input_field.display:
                break
        assert input_field.display
        assert screen._current_prompt is not None
        assert screen._current_prompt.key == "VAULT_ADDR"

        screen.submit_current_prompt("test-value")

        status = screen.query_one("#secrets-prompt-status", Static)
        assert "Awaiting next prompt" in str(status.renderable)


@pytest.mark.asyncio
async def test_secrets_onboard_infisical_first_prompt(tmp_path) -> None:
    ctx = CLIContext(project_root=tmp_path)
    async with _TestApp(ctx, skip_automation=True).run_test() as pilot:
        await pilot.pause()
        screen = cast(SecretsOnboardScreen, pilot.app.screen)
        await pilot.click("#provider-infisical_cloud")
        await pilot.click("#secrets-start")

        input_field = cast(Input, screen.query_one("#secrets-input"))
        for _ in range(50):
            await pilot.pause(0.1)
            if input_field.display:
                break
        assert input_field.display
        assert screen._current_prompt is not None
        assert screen._current_prompt.key == "INFISICAL_BASE_URL"
