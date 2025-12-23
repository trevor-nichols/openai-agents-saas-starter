from __future__ import annotations

from dataclasses import dataclass

from starter_cli.ports.presentation import (
    NotifyPort,
    NullProgress,
    Presenter,
    ProgressPort,
    PromptPort,
)


@dataclass(slots=True)
class TextualPresenter(Presenter):
    """Presenter adapter for Textual-driven interactive flows."""


def build_textual_presenter(
    *,
    prompt: PromptPort,
    notify: NotifyPort,
    progress: ProgressPort | None = None,
) -> TextualPresenter:
    return TextualPresenter(prompt=prompt, notify=notify, progress=progress or NullProgress())


__all__ = ["TextualPresenter", "build_textual_presenter"]
