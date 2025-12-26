"""Prompt answer recording and export helpers for the setup wizard."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from .inputs import InputProvider, ParsedAnswers, _normalize_key


@runtime_checkable
class _AnswerAware(Protocol):
    @property
    def answers(self) -> ParsedAnswers: ...


class AnswerRecorder:
    """Collects raw prompt responses for optional export."""

    def __init__(self) -> None:
        self._answers: dict[str, str] = {}

    def record(self, key: str, value: str) -> None:
        self._answers[_normalize_key(key)] = value

    def snapshot(self) -> dict[str, str]:
        return dict(self._answers)

    def export(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self._answers, indent=2, sort_keys=True)
        path.write_text(payload + "\n", encoding="utf-8")


@dataclass(slots=True)
class RecordingInputProvider(InputProvider):
    """InputProvider wrapper that records every response."""

    provider: InputProvider
    recorder: AnswerRecorder

    def prompt_string(
        self,
        *,
        key: str,
        prompt: str,
        default: str | None,
        required: bool,
    ) -> str:
        value = self.provider.prompt_string(
            key=key,
            prompt=prompt,
            default=default,
            required=required,
        )
        self.recorder.record(key, value)
        return value

    @property
    def answers(self) -> ParsedAnswers:
        if isinstance(self.provider, _AnswerAware):
            return self.provider.answers
        raise AttributeError("answers not available")

    def prompt_bool(self, *, key: str, prompt: str, default: bool) -> bool:
        value = self.provider.prompt_bool(key=key, prompt=prompt, default=default)
        self.recorder.record(key, "true" if value else "false")
        return value

    def prompt_choice(
        self,
        *,
        key: str,
        prompt: str,
        choices,
        default: str | None = None,
    ) -> str:
        value = self.provider.prompt_choice(
            key=key,
            prompt=prompt,
            choices=choices,
            default=default,
        )
        self.recorder.record(key, value)
        return value

    def prompt_secret(
        self,
        *,
        key: str,
        prompt: str,
        existing: str | None,
        required: bool,
    ) -> str:
        value = self.provider.prompt_secret(
            key=key,
            prompt=prompt,
            existing=existing,
            required=required,
        )
        self.recorder.record(key, value)
        return value


__all__ = ["AnswerRecorder", "RecordingInputProvider"]
