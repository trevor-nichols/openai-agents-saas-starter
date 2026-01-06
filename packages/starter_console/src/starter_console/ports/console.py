from __future__ import annotations

import os
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
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
    stream: TextIO = field(default_factory=lambda: sys.stdout)
    err_stream: TextIO = field(default_factory=lambda: sys.stderr)

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
        header = self._format_prompt_header(
            prompt=prompt,
            key=key,
            default=default if not secret else None,
            suffix=None,
        )
        hint = f"{header}\n{self._style('>', 'cyan')} "
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
        header = self._format_prompt_header(
            prompt=prompt,
            key=key,
            default=None,
            suffix=f"(y/n, default: {label})",
        )
        hint = f"{header}\n{self._style('>', 'cyan')} "
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
        label = self._style(f"[{level}]", _LEVEL_STYLES.get(level, "dim"))
        topic_label = self._style(f"[{topic}]", "dim") if topic else ""
        stream.write(f"{timestamp} {label}{topic_label} {message}\n")

    def _style(self, text: str, style: str) -> str:
        if not _color_enabled(self.stream):
            return text
        return f"{_STYLES.get(style, '')}{text}{_RESET}"

    def _format_prompt_header(
        self,
        *,
        prompt: str,
        key: str,
        default: str | None,
        suffix: str | None,
    ) -> str:
        parts: list[str] = [self._style("?", "cyan"), self._style(prompt, "bold")]
        parts.append(self._style(f"[{key}]", "dim"))
        if default:
            parts.append(self._style(f"(default: {default})", "dim"))
        if suffix:
            parts.append(self._style(suffix, "dim"))
        return " ".join(parts)


_RESET = "\033[0m"
_STYLES = {
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "cyan": "\033[36m",
}

_LEVEL_STYLES = {
    "INFO": "cyan",
    "WARN": "yellow",
    "ERROR": "red",
    "SUCCESS": "green",
    "NOTE": "blue",
}


def _color_enabled(stream: TextIO) -> bool:
    if os.getenv("NO_COLOR"):
        return False
    override = os.getenv("STARTER_CONSOLE_COLOR", "1").strip().lower()
    if override in {"0", "false", "no"}:
        return False
    try:
        return stream.isatty()
    except Exception:  # pragma: no cover - defensive
        return False
