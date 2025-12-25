from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, TextIO

from starter_cli.ports.console import ConsolePort
from starter_cli.ports.presentation import Presenter


@dataclass(slots=True)
class PresenterConsoleAdapter(ConsolePort):
    """Bridge a Presenter into the ConsolePort API used by workflow runners."""

    presenter: Presenter
    stream: TextIO = sys.stdout
    err_stream: TextIO = sys.stderr

    def info(self, message: str, topic: str | None = None, *, stream: TextIO | None = None) -> None:
        self.presenter.notify.info(message, topic, stream=stream)

    def warn(self, message: str, topic: str | None = None, *, stream: TextIO | None = None) -> None:
        self.presenter.notify.warn(message, topic, stream=stream)

    def error(
        self, message: str, topic: str | None = None, *, stream: TextIO | None = None
    ) -> None:
        self.presenter.notify.error(message, topic, stream=stream)

    def success(
        self, message: str, topic: str | None = None, *, stream: TextIO | None = None
    ) -> None:
        self.presenter.notify.success(message, topic, stream=stream)

    def note(self, message: str, topic: str | None = None) -> None:
        self.presenter.notify.note(message, topic)

    def section(self, title: str, subtitle: str | None = None, *, icon: str = "◆") -> None:
        self.presenter.notify.section(title, subtitle, icon=icon)

    def step(self, prefix: str, message: str) -> None:
        self.presenter.notify.step(prefix, message)

    def value_change(
        self,
        *,
        scope: str | None,
        key: str,
        previous: str | None,
        current: str,
        secret: bool = False,
    ) -> None:
        self.presenter.notify.value_change(
            scope=scope,
            key=key,
            previous=previous,
            current=current,
            secret=secret,
        )

    def newline(self) -> None:
        self.presenter.notify.newline()

    def print(self, *renderables: Any, **kwargs: Any) -> None:
        self.presenter.notify.print(*renderables, **kwargs)

    def render(self, renderable: Any, *, error: bool = False) -> None:
        self.presenter.notify.render(renderable, error=error)

    def rule(self, title: str) -> None:
        self.presenter.notify.rule(title)

    def ask_text(
        self,
        *,
        key: str,
        prompt: str,
        default: str | None,
        required: bool,
        secret: bool = False,
        command_hook=None,
    ) -> str:
        # command_hook is not used by presenter-driven flows; handle UI commands upstream.
        if secret:
            return self.presenter.prompt.prompt_secret(
                key=key,
                prompt=prompt,
                existing=default,
                required=required,
            )
        return self.presenter.prompt.prompt_string(
            key=key,
            prompt=prompt,
            default=default,
            required=required,
        )

    def ask_bool(
        self,
        *,
        key: str,
        prompt: str,
        default: bool,
        command_hook=None,
    ) -> bool:
        return self.presenter.prompt.prompt_bool(key=key, prompt=prompt, default=default)


__all__ = ["PresenterConsoleAdapter"]
