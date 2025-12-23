from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import cast

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Input

from starter_cli.core import CLIContext
from starter_cli.ui.prompting import PromptChannel, PromptRequest
from starter_cli.ui.wizard_pane import WizardLaunchConfig, WizardPane


class _WizardTestApp(App[None]):
    def __init__(self, ctx: CLIContext) -> None:
        self._ctx = ctx
        super().__init__()

    def compose(self) -> ComposeResult:
        yield WizardPane(self._ctx, config=WizardLaunchConfig(auto_start=False))


@dataclass(slots=True)
class _SessionStub:
    prompt_channel: PromptChannel
    done: bool = False


@pytest.mark.asyncio
async def test_wizard_pane_submit_current_prompt(tmp_path) -> None:
    ctx = CLIContext(project_root=tmp_path)
    async with _WizardTestApp(ctx).run_test() as pilot:
        await pilot.pause()
        pane = cast(WizardPane, pilot.app.query_one(WizardPane))
        channel = PromptChannel()
        setattr(pane, "_session", _SessionStub(prompt_channel=channel))

        results: list[str] = []

        def wait_for_prompt() -> None:
            results.append(
                channel.request(
                    PromptRequest(
                        kind="string",
                        key="WIZARD_TEST",
                        prompt="Wizard prompt",
                        default=None,
                        required=True,
                    )
                )
            )

        thread = threading.Thread(target=wait_for_prompt)
        thread.start()

        for _ in range(20):
            pane._poll_prompt()
            await pilot.pause(0.05)
            if pane._current_prompt is not None:
                break

        assert pane._current_prompt is not None
        input_field = cast(Input, pane.query_one("#wizard-input"))
        assert input_field.display

        pane.submit_current_prompt("ok")
        thread.join(timeout=1)

        assert results == ["ok"]
