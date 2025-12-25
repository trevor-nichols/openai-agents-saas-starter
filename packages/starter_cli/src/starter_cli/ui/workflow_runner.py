from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

from starter_cli.core import CLIContext
from starter_cli.ui.prompt_controller import PromptController
from starter_cli.ui.session_runner import RunnerResult, SessionRunner

T = TypeVar("T")


WorkflowResult = RunnerResult


class WorkflowRunner(Generic[T]):
    def __init__(
        self,
        *,
        ctx: CLIContext,
        prompt_controller: PromptController,
        on_status: Callable[[str], None],
        on_output: Callable[[str], None],
        on_complete: Callable[[WorkflowResult[T]], None] | None = None,
        on_state_change: Callable[[bool], None] | None = None,
    ) -> None:
        self._prompt_controller = prompt_controller
        self._runner = SessionRunner(
            ctx=ctx,
            on_status=on_status,
            on_output=on_output,
            on_complete=on_complete,
            on_state_change=on_state_change,
        )

    @property
    def running(self) -> bool:
        return self._runner.running

    def start(self, label: str, runner: Callable[[CLIContext], T]) -> bool:
        def _on_start(session) -> None:
            self._prompt_controller.set_channel(session.prompt_channel)

        started = self._runner.start(label, runner, on_start=_on_start)
        if started:
            self._prompt_controller.set_status(f"{label} running. Awaiting prompts...")
        return started

    def poll_prompt(self) -> None:
        self._prompt_controller.poll()

    def refresh_output(self) -> None:
        self._runner.refresh_output()
