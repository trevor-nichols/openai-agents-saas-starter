from __future__ import annotations

import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import TextIO

from rich.console import Console as RichConsole
from rich.console import RenderableType
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

_THEMES: dict[str, Theme] = {
    "midnight": Theme(
        {
            "log.time": "#949494",
            "log.topic": "bold cyan",
            "log.level.info": "cyan",
            "log.level.warn": "yellow",
            "log.level.error": "bold red",
            "log.level.success": "bold green",
            "log.message": "white",
            "log.note": "#c7c7c7",
            "section.title": "bold white",
            "section.subtitle": "#b3b3b3",
            "section.rule": "#636363",
            "prompt.border": "#8a8a8a",
            "prompt.label": "bold white",
            "prompt.meta": "#b3b3b3",
            "prompt.hint": "#999999",
            "prompt.input": "cyan",
            "step.text": "white",
            "step.number": "bold cyan",
            "value.key": "bold cyan",
            "value.scope": "#a6a6a6",
            "value.old": "#b3b3b3",
            "value.new": "bold green",
        }
    ),
    "light": Theme(
        {
            "log.time": "#757575",
            "log.topic": "bold blue",
            "log.level.info": "blue",
            "log.level.warn": "dark_orange",
            "log.level.error": "red",
            "log.level.success": "green",
            "log.message": "#121212",
            "log.note": "#5e5e5e",
            "section.title": "black",
            "section.subtitle": "#575757",
            "section.rule": "#999999",
            "prompt.border": "#b3b3b3",
            "prompt.label": "black",
            "prompt.meta": "#4d4d4d",
            "prompt.hint": "#5e5e5e",
            "prompt.input": "blue",
            "step.text": "#121212",
            "step.number": "blue",
            "value.key": "blue",
            "value.scope": "#4d4d4d",
            "value.old": "#707070",
            "value.new": "green",
        }
    ),
    "contrast": Theme(
        {
            "log.time": "bright_white",
            "log.topic": "bold bright_cyan",
            "log.level.info": "bright_cyan",
            "log.level.warn": "bright_yellow",
            "log.level.error": "bright_red",
            "log.level.success": "bright_green",
            "log.message": "bright_white",
            "log.note": "#c7c7c7",
            "section.title": "bright_white",
            "section.subtitle": "bright_white",
            "section.rule": "#a9a9a9",
            "prompt.border": "bright_white",
            "prompt.label": "bright_white",
            "prompt.meta": "#d6d6d6",
            "prompt.hint": "#b3b3b3",
            "prompt.input": "bright_white",
            "step.text": "bright_white",
            "step.number": "bright_white",
            "value.key": "bright_white",
            "value.scope": "#b3b3b3",
            "value.old": "#b3b3b3",
            "value.new": "bright_green",
        }
    ),
}

AVAILABLE_THEMES: tuple[str, ...] = tuple(_THEMES.keys())
_DEFAULT_THEME = "midnight"
_ICON_MAP = {
    "INFO": "i",
    "WARN": "!",
    "ERROR": "x",
    "SUCCESS": "*",
    "NOTE": "-",
}


@dataclass(slots=True)
class _ConsoleSettings:
    theme: str = _DEFAULT_THEME
    width: int | None = None
    no_color: bool = False

    @classmethod
    def from_env(cls) -> _ConsoleSettings:
        theme = os.getenv("STARTER_CLI_THEME", _DEFAULT_THEME).lower()
        width_raw = os.getenv("STARTER_CLI_CONSOLE_WIDTH")
        width = int(width_raw) if width_raw and width_raw.isdigit() else None
        no_color = os.getenv("STARTER_CLI_NO_COLOR", "0").lower() in {"1", "true", "yes"}
        if theme not in AVAILABLE_THEMES:
            theme = _DEFAULT_THEME
        return cls(theme=theme, width=width, no_color=no_color)


class Console:
    """Rich-backed console helper with themed output and prompt helpers."""

    def __init__(self, stream: TextIO = sys.stdout, err_stream: TextIO = sys.stderr) -> None:
        self.stream = stream
        self.err_stream = err_stream
        self._settings = _ConsoleSettings.from_env()
        self._rich_out = self._build_rich_console(stream)
        self._rich_err = self._build_rich_console(err_stream)

    def configure(
        self,
        *,
        theme: str | None = None,
        width: int | None = None,
        no_color: bool | None = None,
    ) -> None:
        updated = _ConsoleSettings(
            theme=(theme or self._settings.theme).lower(),
            width=self._settings.width if width is None else width,
            no_color=self._settings.no_color if no_color is None else no_color,
        )
        if updated.theme not in AVAILABLE_THEMES:
            updated.theme = _DEFAULT_THEME
        self._settings = updated
        self._rich_out = self._build_rich_console(self.stream)
        self._rich_err = self._build_rich_console(self.err_stream)

    def _build_rich_console(self, file: TextIO) -> RichConsole:
        theme = _THEMES[self._settings.theme]
        return RichConsole(
            file=file,
            soft_wrap=True,
            highlight=False,
            color_system=None if self._settings.no_color else "auto",
            no_color=self._settings.no_color,
            theme=theme,
            width=self._settings.width,
        )

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

    def rule(self, title: str) -> None:
        self._rich_out.rule(title, style="section.rule")

    def note(self, message: str, topic: str | None = None) -> None:
        self._log("NOTE", message, topic, self.stream)

    def newline(self) -> None:
        self._rich_out.print()

    def render(self, renderable: RenderableType, *, error: bool = False) -> None:
        target = self._rich_err if error else self._rich_out
        target.print(renderable)

    def section(self, title: str, subtitle: str | None = None, *, icon: str = "◆") -> None:
        text = Text(f"{icon} {title}", style="section.title")
        self._rich_out.print(Rule(text, style="section.rule"))
        if subtitle:
            self._rich_out.print(Text(subtitle, style="section.subtitle"))

    def step(self, prefix: str, message: str) -> None:
        body = Text()
        body.append(prefix, style="step.number")
        body.append("  ")
        body.append(message, style="step.text")
        self._rich_out.print(body)

    def value_change(
        self,
        *,
        scope: str | None,
        key: str,
        previous: str | None,
        current: str,
        secret: bool = False,
    ) -> None:
        table = Table.grid(padding=(0, 1), expand=False)
        table.add_column(justify="right", style="value.scope")
        table.add_column(style="value.new")
        prev_display = "<unset>" if not previous else ("***" if secret else previous)
        next_display = "***" if secret else current
        table.add_row("previous", Text(prev_display, style="value.old"))
        table.add_row("updated", Text(next_display, style="value.new"))
        scope_label = f"[{scope}] " if scope else ""
        label = Text(f"{scope_label}{key}", style="value.key")
        self._rich_out.print(Panel(table, title=label, border_style="prompt.border"))

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
        self._render_prompt_header(
            key=key,
            prompt=prompt,
            default=default,
            required=required,
            secret=secret,
        )
        show_default = False if secret else default is not None
        while True:
            raw_value = Prompt.ask(
                Text(">", style="prompt.input"),
                console=self._rich_out,
                default=default,
                show_default=show_default,
                password=secret,
            )
            if raw_value is None:
                raw_value = ""
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
        self._render_prompt_header(
            key=key,
            prompt=prompt,
            default="yes" if default else "no",
            required=False,
        )
        hint = Text("[y/n] >", style="prompt.input")
        while True:
            raw_value = self._rich_out.input(hint)
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

    def _render_prompt_header(
        self,
        *,
        key: str,
        prompt: str,
        default: str | None,
        required: bool,
        secret: bool = False,
    ) -> None:
        grid = Table.grid(expand=True)
        grid.add_column()
        grid.add_row(Text(prompt, style="prompt.label"))
        meta_parts: list[str] = [f"Key: {key}"]
        meta_parts.append("Required" if required else "Optional")
        if default:
            default_label = "<hidden>" if secret else default
            meta_parts.append(f"Default: {default_label}")
        if secret:
            meta_parts.append("Secret")
        meta = "  •  ".join(meta_parts)
        grid.add_row(Text(meta, style="prompt.meta"))
        self._rich_out.print(Panel(grid, border_style="prompt.border"))

    def _log(self, level: str, message: str, topic: str | None, stream: TextIO) -> None:
        console = self._rich_out if stream is self.stream else self._rich_err
        icon = _ICON_MAP.get(level, "•")
        timestamp = datetime.now().strftime("%H:%M:%S")
        text = Text()
        text.append(timestamp, style="log.time")
        if topic:
            text.append(f"  [{topic}]", style="log.topic")
        level_style = f"log.level.{level.lower()}"
        if level == "NOTE":
            level_style = "log.level.info"
        text.append(f"  {icon} ", style=level_style)
        style = "log.message" if level != "NOTE" else "log.note"
        text.append(message, style=style)
        console.print(text)


console = Console()


def configure_console(
    *,
    theme: str | None = None,
    width: int | None = None,
    no_color: bool | None = None,
) -> None:
    console.configure(theme=theme, width=width, no_color=no_color)


__all__ = ["console", "configure_console", "AVAILABLE_THEMES"]
