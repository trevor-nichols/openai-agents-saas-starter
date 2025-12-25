from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, get_args, get_origin

from pydantic_core import PydanticUndefined
from starter_contracts.config import get_settings_class

from starter_cli.core.inventory import WIZARD_PROMPTED_ENV_VARS


@dataclass(slots=True)
class FieldSpec:
    env_var: str
    field_name: str
    type_hint: str
    default: Any
    required: bool
    description: str
    wizard_prompted: bool

    def to_dict(self) -> dict[str, Any]:
        default_value = None if self.default is PydanticUndefined else self.default
        return {
            "env_var": self.env_var,
            "field": self.field_name,
            "type": self.type_hint,
            "default": default_value,
            "required": self.required,
            "wizard_prompted": self.wizard_prompted,
            "description": self.description,
        }


def collect_field_specs(settings_cls: type | None = None) -> list[FieldSpec]:
    settings_cls = settings_cls or get_settings_class()
    specs: list[FieldSpec] = []
    for field_name, field in getattr(settings_cls, "model_fields", {}).items():
        alias = (field.alias or field_name).upper()
        specs.append(
            FieldSpec(
                env_var=alias,
                field_name=field_name,
                type_hint=_format_annotation(field.annotation),
                default=field.default,
                required=field.is_required(),
                description=(field.description or "").strip().replace("\n", " "),
                wizard_prompted=alias in WIZARD_PROMPTED_ENV_VARS,
            )
        )
    return sorted(specs, key=lambda spec: spec.env_var)


def format_default(value: Any, required: bool) -> str:
    if value is PydanticUndefined:
        return "<required>" if required else ""
    if value is None:
        return ""
    if isinstance(value, str):
        return value or '""'
    return str(value)


def render_markdown(field_specs: list[FieldSpec]) -> str:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S %Z")
    lines = [
        "# Starter CLI Environment Inventory",
        "",
        "This file is generated via `python -m starter_cli.app config write-inventory`.",
        f"Last updated: {timestamp}",
        "",
        "Legend: `✅` = wizard prompts for it, blank = requires manual population.",
        "",
        "| Env Var | Type | Default | Required | Wizard? | Description |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for spec in field_specs:
        default_value = _markdown_escape(format_default(spec.default, spec.required))
        description = _markdown_escape(spec.description)
        lines.append(
            "| {env} | {type} | {default} | {required} | {wizard} | {description} |".format(
                env=spec.env_var,
                type=_markdown_escape(spec.type_hint),
                default=default_value or "—",
                required="✅" if spec.required else "",
                wizard="✅" if spec.wizard_prompted else "",
                description=description or "—",
            )
        )
    return "\n".join(lines).strip() + "\n"


def _format_annotation(annotation: Any) -> str:
    origin = get_origin(annotation)
    if origin is None:
        return getattr(annotation, "__name__", str(annotation))
    args = get_args(annotation)
    if origin is list or origin is tuple or origin is set:
        inner = ", ".join(_format_annotation(arg) for arg in args) or "Any"
        return f"{origin.__name__}[{inner}]"
    if origin is dict:
        key_type, value_type = (*args, "Any", "Any")[:2]
        return f"dict[{_format_annotation(key_type)}, {_format_annotation(value_type)}]"
    if origin is type(None):  # pragma: no cover - defensive
        return "None"
    if origin is Any:
        return "Any"
    inner = " | ".join(_format_annotation(arg) for arg in args) or "Any"
    return inner


def _markdown_escape(value: str | None) -> str:
    if not value:
        return ""
    return value.replace("|", "\\|")


__all__ = ["FieldSpec", "collect_field_specs", "format_default", "render_markdown"]
