from __future__ import annotations

from dataclasses import dataclass

from starter_console.ports.console import ConsolePort
from starter_console.ports.presentation import NullProgress, Presenter, PromptPort


@dataclass(slots=True)
class ConsolePromptAdapter(PromptPort):
    console: ConsolePort

    def prompt_string(
        self,
        *,
        key: str,
        prompt: str,
        default: str | None,
        required: bool,
    ) -> str:
        return self.console.ask_text(
            key=key,
            prompt=prompt,
            default=default,
            required=required,
        )

    def prompt_choice(
        self,
        *,
        key: str,
        prompt: str,
        choices: tuple[str, ...] | list[str],
        default: str | None = None,
    ) -> str:
        choice_list = list(choices)
        while True:
            value = self.console.ask_text(
                key=key,
                prompt=f"{prompt} [{'/'.join(choice_list)}]",
                default=default,
                required=True,
            )
            if value in choice_list:
                return value
            self.console.warn(
                f"Invalid choice '{value}'. Valid options: {', '.join(choice_list)}.",
                topic="prompt",
            )

    def prompt_bool(self, *, key: str, prompt: str, default: bool) -> bool:
        return self.console.ask_bool(key=key, prompt=prompt, default=default)

    def prompt_secret(
        self,
        *,
        key: str,
        prompt: str,
        existing: str | None,
        required: bool,
    ) -> str:
        return self.console.ask_text(
            key=key,
            prompt=prompt,
            default=existing,
            required=required and not existing,
            secret=True,
        )


def build_headless_presenter(console: ConsolePort) -> Presenter:
    prompt = ConsolePromptAdapter(console=console)
    return Presenter(prompt=prompt, notify=console, progress=NullProgress())


__all__ = ["ConsolePromptAdapter", "build_headless_presenter"]
