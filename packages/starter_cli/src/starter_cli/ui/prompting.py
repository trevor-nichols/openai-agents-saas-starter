from __future__ import annotations

import queue
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from starter_cli.core import CLIError
from starter_cli.workflows.setup.inputs import ParsedAnswers


@dataclass(slots=True, frozen=True)
class PromptRequest:
    kind: Literal["string", "secret", "bool", "choice"]
    key: str
    prompt: str
    default: str | None
    required: bool
    choices: tuple[str, ...] = ()


class PromptChannel:
    def __init__(self) -> None:
        self._requests: queue.Queue[PromptRequest] = queue.Queue()
        self._responses: queue.Queue[str] = queue.Queue()
        self._current: PromptRequest | None = None

    def request(self, request: PromptRequest) -> str:
        self._requests.put(request)
        return self._responses.get()

    def poll(self) -> PromptRequest | None:
        if self._current is not None:
            return None
        try:
            self._current = self._requests.get_nowait()
        except queue.Empty:
            return None
        return self._current

    def current(self) -> PromptRequest | None:
        return self._current

    def submit(self, value: str) -> None:
        if self._current is None:
            return
        self._current = None
        self._responses.put(value)


class TextualPromptPort:
    def __init__(
        self,
        *,
        prefill: ParsedAnswers | Mapping[str, str],
        channel: PromptChannel,
    ) -> None:
        self.prefill = {key.strip().upper(): value for key, value in dict(prefill).items()}
        self.channel = channel

    def prompt_string(
        self,
        *,
        key: str,
        prompt: str,
        default: str | None,
        required: bool,
    ) -> str:
        value = self._pop_prefill(key)
        if value is not None:
            return value
        request = PromptRequest(
            kind="string",
            key=key,
            prompt=prompt,
            default=default,
            required=required,
        )
        return self.channel.request(request)

    def prompt_bool(self, *, key: str, prompt: str, default: bool) -> bool:
        value = self._pop_prefill(key)
        if value is not None:
            return _coerce_bool(value, key)
        request = PromptRequest(
            kind="bool",
            key=key,
            prompt=prompt,
            default="yes" if default else "no",
            required=True,
            choices=("yes", "no"),
        )
        response = self.channel.request(request)
        return _coerce_bool(response, key)

    def prompt_choice(
        self,
        *,
        key: str,
        prompt: str,
        choices: Sequence[str],
        default: str | None = None,
    ) -> str:
        value = self._pop_prefill(key)
        if value is not None:
            if value not in choices:
                raise CLIError(f"Invalid choice for {key}: {value} (expected one of {choices})")
            return value
        request = PromptRequest(
            kind="choice",
            key=key,
            prompt=prompt,
            default=default,
            required=True,
            choices=tuple(choices),
        )
        response = self.channel.request(request)
        if response not in choices:
            raise CLIError(f"Invalid choice for {key}: {response} (expected one of {choices})")
        return response

    def prompt_secret(
        self,
        *,
        key: str,
        prompt: str,
        existing: str | None,
        required: bool,
    ) -> str:
        value = self._pop_prefill(key)
        if value is not None:
            return value
        request = PromptRequest(
            kind="secret",
            key=key,
            prompt=prompt,
            default=existing,
            required=required and not existing,
        )
        response = self.channel.request(request)
        if response:
            return response
        return existing or ""

    def _pop_prefill(self, key: str) -> str | None:
        return self.prefill.pop(key.strip().upper(), None)


def _coerce_bool(value: str, key: str) -> bool:
    raw = value.strip().lower()
    if raw in {"1", "true", "yes", "y"}:
        return True
    if raw in {"0", "false", "no", "n"}:
        return False
    raise CLIError(f"Invalid boolean for {key}: {value}")


__all__ = ["PromptChannel", "PromptRequest", "TextualPromptPort"]
