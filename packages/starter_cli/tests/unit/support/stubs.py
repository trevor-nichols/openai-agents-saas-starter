from __future__ import annotations

from dataclasses import dataclass, field

from starter_cli.core import CLIError
from starter_cli.workflows.setup.inputs import InputProvider


@dataclass(slots=True)
class StubInputProvider(InputProvider):
    strings: dict[str, str] = field(default_factory=dict)
    bools: dict[str, bool] = field(default_factory=dict)
    secrets: dict[str, str] = field(default_factory=dict)

    def prompt_string(
        self,
        *,
        key: str,
        prompt: str,
        default: str | None,
        required: bool,
    ) -> str:
        if key in self.strings:
            return self.strings[key]
        if default is not None:
            return default
        if required:
            raise CLIError(f"Missing required value for {key}")
        return ""

    def prompt_bool(self, *, key: str, prompt: str, default: bool) -> bool:
        return self.bools.get(key, default)

    def prompt_secret(
        self,
        *,
        key: str,
        prompt: str,
        existing: str | None,
        required: bool,
    ) -> str:
        if key in self.secrets:
            return self.secrets[key]
        if existing:
            return existing
        if required:
            raise CLIError(f"Missing required secret for {key}")
        return ""

    def prompt_choice(
        self,
        *,
        key: str,
        prompt: str,
        choices,
        default: str | None = None,
    ) -> str:
        value = self.strings.get(key, default or (choices[0] if choices else ""))
        if value not in choices:
            raise CLIError(f"Invalid choice for {key}")
        return value
