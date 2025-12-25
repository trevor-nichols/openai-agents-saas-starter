from __future__ import annotations

import pytest
from textual.app import App, ComposeResult
from textual.widgets import RadioButton, RadioSet, Static

from starter_console.core import CLIContext
from starter_console.ui.wizard_pane import WizardLaunchConfig, WizardPane


class WizardPaneApp(App[None]):
    def __init__(self, ctx: CLIContext, config: WizardLaunchConfig) -> None:
        super().__init__()
        self._ctx = ctx
        self._config = config

    def compose(self) -> ComposeResult:
        yield WizardPane(self._ctx, config=self._config)


@pytest.mark.asyncio
async def test_wizard_pane_cloud_controls_toggle(tmp_path) -> None:
    ctx = CLIContext(project_root=tmp_path)
    config = WizardLaunchConfig(profile="demo")
    app = WizardPaneApp(ctx, config)

    async with app.run_test() as pilot:
        pane = app.query_one(WizardPane)
        assert pane is not None

        cloud_label = app.query_one("#wizard-cloud-label", Static)
        cloud_radio = app.query_one("#wizard-cloud", RadioSet)
        summary = app.query_one("#wizard-summary", Static)

        assert cloud_label.display is False
        assert cloud_radio.display is False
        assert "Preset: local_docker" in str(summary.renderable)

        app.query_one("#preset-cloud", RadioButton).value = True
        await pilot.pause()

        assert cloud_label.display is True
        assert cloud_radio.display is True
        assert "Preset: cloud_managed" in str(summary.renderable)
