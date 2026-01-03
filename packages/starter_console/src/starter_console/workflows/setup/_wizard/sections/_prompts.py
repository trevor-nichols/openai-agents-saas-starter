from __future__ import annotations

from starter_console.core import CLIError

from ...inputs import InputProvider, is_headless_provider
from ..context import WizardContext


def prompt_nonempty_string(
    context: WizardContext,
    provider: InputProvider,
    *,
    key: str,
    prompt: str,
    default: str,
    topic: str = "wizard",
) -> str:
    while True:
        value = provider.prompt_string(
            key=key,
            prompt=prompt,
            default=default,
            required=True,
        ).strip()
        if value:
            return value
        if is_headless_provider(provider):
            raise CLIError(f"{key} cannot be blank.")
        context.console.warn(f"{key} cannot be blank.", topic=topic)


def prompt_port(
    context: WizardContext,
    provider: InputProvider,
    *,
    key: str,
    prompt: str,
    default: str,
    topic: str = "wizard",
) -> int:
    while True:
        raw = provider.prompt_string(
            key=key,
            prompt=prompt,
            default=default,
            required=True,
        ).strip()
        try:
            port = int(raw)
        except ValueError as exc:
            if is_headless_provider(provider):
                raise CLIError(f"{key} must be an integer.") from exc
            context.console.warn(f"{key} must be an integer.", topic=topic)
            continue
        if 1 <= port <= 65535:
            return port
        if is_headless_provider(provider):
            raise CLIError(f"{key} must be between 1 and 65535.")
        context.console.warn(f"{key} must be between 1 and 65535.", topic=topic)


__all__ = ["prompt_nonempty_string", "prompt_port"]
