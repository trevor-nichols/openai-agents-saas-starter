from __future__ import annotations

import io

from starter_console.ports.presentation import NotifyPort
from starter_console.workflows.setup.ui import WizardUIView


class WizardNotifyPort(NotifyPort):
    def __init__(self, ui: WizardUIView) -> None:
        self._ui = ui
        self.stream = io.StringIO()
        self.err_stream = io.StringIO()

    def info(self, message: str, topic: str | None = None, *, stream=None) -> None:
        self._log("INFO", message, topic)

    def warn(self, message: str, topic: str | None = None, *, stream=None) -> None:
        self._log("WARN", message, topic)

    def error(self, message: str, topic: str | None = None, *, stream=None) -> None:
        self._log("ERROR", message, topic)

    def success(self, message: str, topic: str | None = None, *, stream=None) -> None:
        self._log("SUCCESS", message, topic)

    def note(self, message: str, topic: str | None = None) -> None:
        self._log("NOTE", message, topic)

    def section(self, title: str, subtitle: str | None = None, *, icon: str = "*") -> None:
        line = f"{icon} {title}"
        if subtitle:
            line += f" - {subtitle}"
        self._ui.log(line)

    def step(self, prefix: str, message: str) -> None:
        self._ui.log(f"{prefix} {message}")

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
        self._ui.log(f"{scope_label}{key}: {prev_display} -> {next_display}")

    def newline(self) -> None:
        self._ui.log("")

    def print(self, *renderables, **kwargs) -> None:
        joined = " ".join(str(item) for item in renderables)
        self._ui.log(joined)

    def render(self, renderable, *, error: bool = False) -> None:
        self._ui.log(str(renderable))

    def rule(self, title: str) -> None:
        self._ui.log(f"---- {title} ----")

    def _log(self, level: str, message: str, topic: str | None) -> None:
        topic_label = f"[{topic}]" if topic else ""
        self._ui.log(f"[{level}]{topic_label} {message}")


__all__ = ["WizardNotifyPort"]
