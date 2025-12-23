from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from getpass import getpass
from typing import Any, Protocol, TextIO

from .presentation import NotifyPort


class ConsolePort(NotifyPort, Protocol):
    stream: TextIO
    err_stream: TextIO

    def info(
        self,
        message: str,
        topic: str | None = None,
        *,
        stream: TextIO | None = None,
    ) -> None: ...
    def warn(
        self,
        message: str,
        topic: str | None = None,
        *,
        stream: TextIO | None = None,
    ) -> None: ...
    def error(
        self,
        message: str,
        topic: str | None = None,
        *,
        stream: TextIO | None = None,
    ) -> None: ...
    def success(
        self,
        message: str,
        topic: str | None = None,
        *,
        stream: TextIO | None = None,
    ) -> None: ...
    def note(self, message: str, topic: str | None = None) -> None: ...
    def section(
        self,
        title: str,
        subtitle: str | None = None,
        *,
        icon: str = "◆",
    ) -> None: ...
    def step(self, prefix: str, message: str) -> None: ...
    def value_change(
        self,
        *,
        scope: str | None,
        key: str,
        previous: str | None,
        current: str,
        secret: bool = False,
    ) -> None: ...
    def newline(self) -> None: ...
    def print(self, *renderables: Any, **kwargs: Any) -> None: ...
    def render(self, renderable: Any, *, error: bool = False) -> None: ...
    def rule(self, title: str) -> None: ...
    def ask_text(
        self,
        *,
        key: str,
        prompt: str,
        default: str | None,
        required: bool,
        secret: bool = False,
        command_hook: Callable[[str], bool] | None = None,
    ) -> str: ...
    def ask_bool(
        self,
        *,
        key: str,
        prompt: str,
        default: bool,
        command_hook: Callable[[str], bool] | None = None,
    ) -> bool: ...


@dataclass(slots=True)
class StdConsole(ConsolePort):
    stream: TextIO = sys.stdout
    err_stream: TextIO = sys.stderr

    def info(
        self,
        message: str,
        topic: str | None = None,
        *,
        stream: TextIO | None = None,
    ) -> None:
        self._log("INFO", message, topic, stream or self.stream)

    def warn(
        self,
        message: str,
        topic: str | None = None,
        *,
        stream: TextIO | None = None,
    ) -> None:
        self._log("WARN", message, topic, stream or self.err_stream)

    def error(
        self,
        message: str,
        topic: str | None = None,
        *,
        stream: TextIO | None = None,
    ) -> None:
        self._log("ERROR", message, topic, stream or self.err_stream)

    def success(
        self,
        message: str,
        topic: str | None = None,
        *,
        stream: TextIO | None = None,
    ) -> None:
        self._log("SUCCESS", message, topic, stream or self.stream)

    def note(self, message: str, topic: str | None = None) -> None:
        self._log("NOTE", message, topic, self.stream)

    def section(self, title: str, subtitle: str | None = None, *, icon: str = "◆") -> None:
        line = f"{icon} {title}"
        self.stream.write(f"\n{line}\n")
        if subtitle:
            self.stream.write(f"{subtitle}\n")

    def step(self, prefix: str, message: str) -> None:
        self.stream.write(f"{prefix} {message}\n")

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
        self.stream.write(
            f"{scope_label}{key}: {prev_display} -> {next_display}\n"
        )

    def newline(self) -> None:
        self.stream.write("\n")

    def print(self, *renderables: Any, **kwargs: Any) -> None:
        print(*renderables, file=self.stream, **kwargs)

    def render(self, renderable: Any, *, error: bool = False) -> None:
        target = self.err_stream if error else self.stream
        print(renderable, file=target)

    def rule(self, title: str) -> None:
        self.stream.write(f"{'-' * 4} {title} {'-' * 4}\n")

    def ask_text(
        self,
        *,
        key: str,
        prompt: str,
        default: str | None,
        required: bool,
        secret: bool = False,
        command_hook: Callable[[str], bool] | None = None,
    ) -> str:
        hint = f"{prompt} [{key}]"
        if default and not secret:
            hint += f" (default: {default})"
        hint += ": "
        while True:
            raw_value = getpass(hint) if secret else input(hint)
            if command_hook and command_hook(raw_value):
                continue
            value = raw_value.strip()
            if value:
                return value
            if default is not None:
                return default
            if not required:
                return ""
            self.warn("A value is required for this field.", topic="prompt")

    def ask_bool(
        self,
        *,
        key: str,
        prompt: str,
        default: bool,
        command_hook: Callable[[str], bool] | None = None,
    ) -> bool:
        label = "y" if default else "n"
        hint = f"{prompt} [{key}] (y/n, default: {label}): "
        while True:
            raw_value = input(hint)
            if command_hook and command_hook(raw_value):
                continue
            raw = raw_value.strip().lower()
            if not raw:
                return default
            if raw in {"y", "yes"}:
                return True
            if raw in {"n", "no"}:
                return False
            self.warn("Please enter y or n.", topic="prompt")

    def _log(self, level: str, message: str, topic: str | None, stream: TextIO) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        label = f"[{level}]"
        topic_label = f"[{topic}]" if topic else ""
        stream.write(f"{timestamp} {label}{topic_label} {message}\n")
