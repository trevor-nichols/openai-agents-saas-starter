from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

from starter_cli.core import CLIContext
from starter_cli.ui.workflow_session import InteractiveWorkflowSession, render_log_lines

T = TypeVar("T")


@dataclass(slots=True)
class RunnerResult(Generic[T]):
    label: str
    value: T | None
    error: Exception | None


class SessionRunner(Generic[T]):
    def __init__(
        self,
        *,
        ctx: CLIContext,
        on_status: Callable[[str], None],
        on_output: Callable[[str], None],
        on_complete: Callable[[RunnerResult[T]], None] | None = None,
        on_state_change: Callable[[bool], None] | None = None,
    ) -> None:
        self._ctx = ctx
        self._on_status = on_status
        self._on_output = on_output
        self._on_complete = on_complete
        self._on_state_change = on_state_change
        self._session: InteractiveWorkflowSession[T] | None = None
        self._active_label: str | None = None
        self._session_handled = False
        self._last_log: tuple[str, ...] = ()

    @property
    def running(self) -> bool:
        return bool(self._session and self._session.running)

    def start(
        self,
        label: str,
        runner: Callable[[CLIContext], T],
        *,
        on_start: Callable[[InteractiveWorkflowSession[T]], None] | None = None,
        start_status: str | None = None,
    ) -> bool:
        if self.running:
            return False
        self._session = InteractiveWorkflowSession(self._ctx, runner=runner)
        self._active_label = label
        self._session_handled = False
        self._last_log = ()
        if on_start:
            on_start(self._session)
        if start_status is not None:
            self._on_status(start_status)
        if self._on_state_change:
            self._on_state_change(True)
        self._session.start()
        return True

    def refresh_output(self) -> None:
        if not self._session:
            return
        lines = self._session.log.snapshot()
        if lines != self._last_log:
            self._on_output(render_log_lines(lines))
            self._last_log = lines
        if self._session.done and not self._session_handled:
            self._handle_complete()

    def _handle_complete(self) -> None:
        if not self._session:
            return
        self._session_handled = True
        label = self._active_label or "Workflow"
        result = RunnerResult(
            label=label,
            value=self._session.result.value,
            error=self._session.result.error,
        )
        if result.error:
            self._on_status(f"{label} failed: {result.error}")
        else:
            self._on_status(f"{label} complete.")
        if self._on_state_change:
            self._on_state_change(False)
        if self._on_complete:
            self._on_complete(result)


__all__ = ["RunnerResult", "SessionRunner"]
