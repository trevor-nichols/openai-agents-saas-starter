from __future__ import annotations

import json
import secrets
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from getpass import getpass
from pathlib import Path
from typing import Protocol

from ..common import CLIError
from ..console import console

ParsedAnswers = dict[str, str]


def _normalize_key(key: str) -> str:
    return key.strip().upper()


def load_answers_files(paths: Sequence[str | Path]) -> ParsedAnswers:
    answers: ParsedAnswers = {}
    for raw in paths:
        path = Path(raw).expanduser().resolve()
        if not path.exists():
            raise CLIError(f"Answers file not found: {path}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - invalid user input
            raise CLIError(f"Invalid JSON in {path}: {exc}") from exc
        if not isinstance(payload, Mapping):
            raise CLIError(f"Answers file {path} must contain an object of key/value pairs.")
        for key, value in payload.items():
            if value is None:
                continue
            answers[_normalize_key(str(key))] = str(value)
    return answers


def merge_answer_overrides(base: ParsedAnswers, overrides: Sequence[str]) -> ParsedAnswers:
    merged = dict(base)
    for override in overrides:
        if "=" not in override:
            raise CLIError(f"Invalid override '{override}'. Expected KEY=VALUE format.")
        key, value = override.split("=", 1)
        merged[_normalize_key(key)] = value
    return merged


class InputProvider(Protocol):
    def prompt_string(
        self,
        *,
        key: str,
        prompt: str,
        default: str | None,
        required: bool,
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


@dataclass(slots=True)
class InteractiveInputProvider(InputProvider):
    prefill: ParsedAnswers

    def prompt_string(self, *, key: str, prompt: str, default: str | None, required: bool) -> str:
        normalized = _normalize_key(key)
        if (value := self.prefill.pop(normalized, None)) is not None:
            console.info(f"{key} supplied via answers file / override.", topic="wizard")
            return value
        while True:
            suffix = f" [{default}]" if default else ""
            value = input(f"{prompt}{suffix}: ").strip()
            if value:
                return value
            if default is not None:
                return default
            if not required:
                return ""
            console.warn("A value is required for this field.")

    def prompt_bool(self, *, key: str, prompt: str, default: bool) -> bool:
        normalized = _normalize_key(key)
        if (value := self.prefill.pop(normalized, None)) is not None:
            return _coerce_bool(value, key)
        hint = "Y/n" if default else "y/N"
        while True:
            raw = input(f"{prompt} ({hint}) ").strip().lower()
            if not raw:
                return default
            if raw in {"y", "yes"}:
                return True
            if raw in {"n", "no"}:
                return False
            console.warn("Please answer yes or no.")

    def prompt_secret(
        self,
        *,
        key: str,
        prompt: str,
        existing: str | None,
        required: bool,
    ) -> str:
        normalized = _normalize_key(key)
        if (value := self.prefill.pop(normalized, None)) is not None:
            console.info(f"{key} supplied via answers file / override.", topic="wizard")
            return value
        if existing:
            console.info(
                f"{prompt} already set; press Enter to keep the current value.",
                topic="wizard",
            )
        while True:
            value = getpass(f"{prompt}: ").strip()
            if value:
                return value
            if existing:
                return existing
            if required:
                console.warn("A value is required for this secret.")
            else:
                console.info("Generating a secure random value …", topic="wizard")
                return secrets.token_urlsafe(32)


@dataclass(slots=True)
class HeadlessInputProvider(InputProvider):
    answers: ParsedAnswers

    def prompt_string(self, *, key: str, prompt: str, default: str | None, required: bool) -> str:
        normalized = _normalize_key(key)
        if (value := self.answers.get(normalized)) is not None:
            return value
        if default is not None:
            return default
        if required:
            raise CLIError(
                "Missing required value for "
                f"{key}. Provide it via --answers-file or --var KEY=VALUE."
            )
        return ""

    def prompt_bool(self, *, key: str, prompt: str, default: bool) -> bool:
        normalized = _normalize_key(key)
        if (value := self.answers.get(normalized)) is None:
            return default
        return _coerce_bool(value, key)

    def prompt_secret(
        self,
        *,
        key: str,
        prompt: str,
        existing: str | None,
        required: bool,
    ) -> str:
        normalized = _normalize_key(key)
        if (value := self.answers.get(normalized)) is not None:
            return value
        if existing:
            return existing
        if required:
            raise CLIError(
                "Missing required secret "
                f"{key}. Provide it via --answers-file or --var KEY=VALUE."
            )
        return ""


def _coerce_bool(value: str, key: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    raise CLIError(
        f"Unable to parse boolean for {key!r}: expected true/false, got '{value}'."
    )
