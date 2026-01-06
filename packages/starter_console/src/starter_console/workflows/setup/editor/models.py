from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as dataclass_field

from starter_console.core import CLIError

from ..inputs import _coerce_bool


@dataclass(slots=True)
class FieldSpec:
    key: str
    label: str
    kind: str
    required: bool
    value: str | None = None
    default: str | None = None
    choices: tuple[str, ...] = ()
    description: str | None = None
    choice_help: dict[str, str] = dataclass_field(default_factory=dict)

    def display_value(self) -> str:
        if self.kind == "secret":
            return "***" if self.value else "<unset>"
        if self.kind == "bool":
            if self.value is None or self.value == "":
                return "<unset>"
            try:
                resolved = _coerce_bool(self.value, self.key)
            except CLIError:
                return self.value
            return "yes" if resolved else "no"
        if self.value is None or self.value == "":
            return "<unset>"
        return self.value

    def is_missing(self) -> bool:
        return self.required and (self.value is None or self.value == "")


@dataclass(slots=True)
class SectionModel:
    key: str
    label: str
    fields: list[FieldSpec]

    @property
    def missing_required(self) -> int:
        return sum(1 for field in self.fields if field.is_missing())


__all__ = ["FieldSpec", "SectionModel"]
