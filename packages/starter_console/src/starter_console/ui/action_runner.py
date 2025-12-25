from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

from starter_console.core import CLIContext
from starter_console.ui.session_runner import RunnerResult, SessionRunner

T = TypeVar("T")


ActionResult = RunnerResult


class ActionRunner(Generic[T]):
    def __init__(
        self,
        *,
        ctx: CLIContext,
        on_status: Callable[[str], None],
        on_output: Callable[[str], None],
        on_complete: Callable[[ActionResult[T]], None] | None = None,
        on_state_change: Callable[[bool], None] | None = None,
    ) -> None:
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
        return self._runner.start(label, runner, start_status=f"{label} running…")

    def refresh_output(self) -> None:
        self._runner.refresh_output()


__all__ = ["ActionResult", "ActionRunner"]
