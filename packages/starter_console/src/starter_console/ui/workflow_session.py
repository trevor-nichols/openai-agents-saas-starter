from __future__ import annotations

import threading
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Generic, TypeVar

from starter_console.core import CLIContext
from starter_console.ports.presentation import NotifyPort
from starter_console.presenters import PresenterConsoleAdapter, build_textual_presenter
from starter_console.ui.context import derive_presenter_context
from starter_console.ui.prompting import PromptChannel, TextualPromptPort

T = TypeVar("T")


class WorkflowLog:
    def __init__(self, *, max_lines: int = 200) -> None:
        self._max_lines = max_lines
        self._lines: list[str] = []
        self._lock = threading.Lock()

    def append(self, line: str) -> None:
        with self._lock:
            self._lines.append(line)
            if len(self._lines) > self._max_lines:
                self._lines = self._lines[-self._max_lines :]

    def snapshot(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(self._lines)


class WorkflowNotifyPort(NotifyPort):
    def __init__(self, log: WorkflowLog) -> None:
        self._log = log

    def info(self, message: str, topic: str | None = None, *, stream=None) -> None:
        self._write("INFO", message, topic)

    def warn(self, message: str, topic: str | None = None, *, stream=None) -> None:
        self._write("WARN", message, topic)

    def error(self, message: str, topic: str | None = None, *, stream=None) -> None:
        self._write("ERROR", message, topic)

    def success(self, message: str, topic: str | None = None, *, stream=None) -> None:
        self._write("SUCCESS", message, topic)

    def note(self, message: str, topic: str | None = None) -> None:
        self._write("NOTE", message, topic)

    def section(self, title: str, subtitle: str | None = None, *, icon: str = "*") -> None:
        line = f"{icon} {title}"
        if subtitle:
            line += f" - {subtitle}"
        self._write("SECTION", line, None)

    def step(self, prefix: str, message: str) -> None:
        self._write("STEP", f"{prefix} {message}", None)

    def value_change(
        self,
        *,
        scope: str | None,
        key: str,
        previous: str | None,
        current: str,
        secret: bool = False,
    ) -> None:
        scope_label = f"[{scope}] " if scope else ""
        prev_display = "<unset>" if previous is None else ("***" if secret else previous)
        next_display = "***" if secret else current
        self._write("VALUE", f"{scope_label}{key}: {prev_display} -> {next_display}", None)

    def newline(self) -> None:
        self._log.append("")

    def print(self, *renderables, **kwargs) -> None:
        joined = " ".join(str(item) for item in renderables)
        self._write("INFO", joined, None)

    def render(self, renderable, *, error: bool = False) -> None:
        level = "ERROR" if error else "INFO"
        self._write(level, str(renderable), None)

    def rule(self, title: str) -> None:
        self._write("RULE", f"---- {title} ----", None)

    def _write(self, level: str, message: str, topic: str | None) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        topic_label = f"[{topic}]" if topic else ""
        self._log.append(f"{stamp} [{level}]{topic_label} {message}")


@dataclass(slots=True)
class WorkflowResult(Generic[T]):
    value: T | None
    error: Exception | None


class InteractiveWorkflowSession(Generic[T]):
    def __init__(
        self,
        ctx: CLIContext,
        *,
        runner: Callable[[CLIContext], T],
        prefill: Mapping[str, str] | None = None,
        max_log_lines: int = 200,
    ) -> None:
        self._ctx = ctx
        self._runner = runner
        self._prefill = prefill or {}
        self._thread: threading.Thread | None = None
        self._done = threading.Event()
        self.prompt_channel = PromptChannel()
        self.log = WorkflowLog(max_lines=max_log_lines)
        self.result = WorkflowResult[T](value=None, error=None)

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def done(self) -> bool:
        return self._done.is_set()

    def start(self) -> None:
        if self.running:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def wait(self, timeout: float | None = None) -> bool:
        return self._done.wait(timeout)

    def _run(self) -> None:
        try:
            notify = WorkflowNotifyPort(self.log)
            prompt = TextualPromptPort(prefill=self._prefill, channel=self.prompt_channel)
            presenter = build_textual_presenter(prompt=prompt, notify=notify)
            console = PresenterConsoleAdapter(presenter)
            workflow_ctx = derive_presenter_context(
                self._ctx,
                console=console,
                presenter=presenter,
            )
            self.result.value = self._runner(workflow_ctx)
        except Exception as exc:  # pragma: no cover - defensive
            self.result.error = exc
            self.log.append(f"{datetime.now().strftime('%H:%M:%S')} [ERROR] {exc}")
        finally:
            self._done.set()


def render_log_lines(lines: Iterable[str], *, limit: int = 80) -> str:
    trimmed = list(lines)[-limit:]
    return "\n".join(trimmed)


__all__ = [
    "InteractiveWorkflowSession",
    "WorkflowLog",
    "WorkflowNotifyPort",
    "WorkflowResult",
    "render_log_lines",
]
