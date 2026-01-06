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
        self._render_choice_list(choice_list, default)
        while True:
            value = self.console.ask_text(
                key=key,
                prompt=prompt,
                default=default,
                required=True,
            )
            normalized = value.strip()
            if normalized.isdigit():
                index = int(normalized)
                if 1 <= index <= len(choice_list):
                    return choice_list[index - 1]
            if normalized in choice_list:
                return normalized
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

    def _render_choice_list(self, choices: list[str], default: str | None) -> None:
        for idx, choice in enumerate(choices, start=1):
            label = f"{idx}) {choice}"
            if choice == default:
                label += " (default)"
            self.console.print(label)


def build_headless_presenter(console: ConsolePort) -> Presenter:
    prompt = ConsolePromptAdapter(console=console)
    return Presenter(prompt=prompt, notify=console, progress=NullProgress())


__all__ = ["ConsolePromptAdapter", "build_headless_presenter"]
