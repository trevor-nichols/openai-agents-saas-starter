from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class NotifyPort(Protocol):
    def info(
        self, message: str, topic: str | None = None, *, stream: Any | None = None
    ) -> None: ...
    def warn(
        self, message: str, topic: str | None = None, *, stream: Any | None = None
    ) -> None: ...
    def error(
        self, message: str, topic: str | None = None, *, stream: Any | None = None
    ) -> None: ...
    def success(
        self, message: str, topic: str | None = None, *, stream: Any | None = None
    ) -> None: ...
    def note(self, message: str, topic: str | None = None) -> None: ...
    def section(self, title: str, subtitle: str | None = None, *, icon: str = "◆") -> None: ...
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


class PromptPort(Protocol):
    def prompt_string(
        self,
        *,
        key: str,
        prompt: str,
        default: str | None,
        required: bool,
    ) -> str: ...

    def prompt_choice(
        self,
        *,
        key: str,
        prompt: str,
        choices: tuple[str, ...] | list[str],
        default: str | None = None,
    ) -> str: ...

    def prompt_bool(self, *, key: str, prompt: str, default: bool) -> bool: ...

    def prompt_secret(
        self,
        *,
        key: str,
        prompt: str,
        existing: str | None,
        required: bool,
    ) -> str: ...


class ProgressPort(Protocol):
    def start(self, *, key: str, total: int | None = None, detail: str | None = None) -> None: ...
    def advance(
        self, *, key: str, completed: int | None = None, detail: str | None = None
    ) -> None: ...
    def finish(self, *, key: str, detail: str | None = None, success: bool = True) -> None: ...


@dataclass(slots=True)
class Presenter:
    prompt: PromptPort
    notify: NotifyPort
    progress: ProgressPort


@dataclass(slots=True)
class NullProgress(ProgressPort):
    def start(self, *, key: str, total: int | None = None, detail: str | None = None) -> None:
        return None

    def advance(
        self,
        *,
        key: str,
        completed: int | None = None,
        detail: str | None = None,
    ) -> None:
        return None

    def finish(self, *, key: str, detail: str | None = None, success: bool = True) -> None:
        return None


__all__ = [
    "NotifyPort",
    "PromptPort",
    "ProgressPort",
    "Presenter",
    "NullProgress",
]
