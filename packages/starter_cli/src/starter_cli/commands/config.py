from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, get_args, get_origin

from pydantic_core import PydanticUndefined
from starter_contracts.config import get_settings_class

from starter_cli.core import CLIContext
from starter_cli.core.inventory import WIZARD_PROMPTED_ENV_VARS
from starter_cli.ports.console import ConsolePort


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    config_parser = subparsers.add_parser("config", help="Inspect backend settings metadata.")
    config_subparsers = config_parser.add_subparsers(dest="config_command")

    dump_parser = config_subparsers.add_parser(
        "dump-schema",
        help="List every backend environment variable with defaults and wizard coverage.",
    )
    dump_parser.add_argument(
        "--format",
        choices={"table", "json"},
        default="table",
        help="Output as aligned table (default) or JSON list.",
    )
    dump_parser.set_defaults(handler=handle_dump_schema)

    inventory_parser = config_subparsers.add_parser(
        "write-inventory",
        help="Render the CLI environment inventory Markdown doc.",
    )
    inventory_parser.add_argument(
        "--path",
        default="docs/trackers/CLI_ENV_INVENTORY.md",
        help=(
            "Destination path for the Markdown inventory "
            "(defaults to docs/trackers/CLI_ENV_INVENTORY.md)."
        ),
    )
    inventory_parser.set_defaults(handler=handle_write_inventory)


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


def handle_dump_schema(args: argparse.Namespace, ctx: CLIContext) -> int:
    console = ctx.console
    settings_cls = get_settings_class()

    field_specs = _collect_field_specs(settings_cls)
    if args.format == "json":
        json_payload = [spec.to_dict() for spec in field_specs]
        json.dump(json_payload, console.stream, indent=2)
        console.stream.write("\n")
        return 0

    _render_table(console, field_specs)
    return 0


def handle_write_inventory(args: argparse.Namespace, ctx: CLIContext) -> int:
    console = ctx.console
    field_specs = _collect_field_specs(get_settings_class())
    destination = Path(args.path).expanduser().resolve()
    body = _render_markdown(field_specs)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(body, encoding="utf-8")
    console.success(f"Environment inventory written to {destination}", topic="config")
    return 0


def _collect_field_specs(settings_cls: type) -> list[FieldSpec]:
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
    # Handle Union/typing.Optional generically.
    if origin is Any:
        return "Any"
    inner = " | ".join(_format_annotation(arg) for arg in args) or "Any"
    return inner


def _format_default(value: Any, required: bool) -> str:
    if value is PydanticUndefined:
        return "<required>" if required else ""
    if value is None:
        return ""
    if isinstance(value, str):
        return value or '""'
    return str(value)


def _render_table(console: ConsolePort, field_specs: list[FieldSpec]) -> None:
    rows = [
        (
            spec.env_var,
            spec.type_hint,
            _format_default(spec.default, spec.required),
            "✅" if spec.wizard_prompted else "",
            "✅" if spec.required else "",
            spec.description,
        )
        for spec in field_specs
    ]
    headers = ("Env Var", "Type", "Default", "Wizard", "Required", "Description")
    widths = [len(header) for header in headers]

    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    def format_row(values: tuple[str, ...]) -> str:
        parts = [value.ljust(widths[idx]) for idx, value in enumerate(values)]
        return " | ".join(parts)

    console.info(format_row(headers), topic="config")
    console.info(format_row(tuple("-" * width for width in widths)), topic="config")
    for row in rows:
        console.info(format_row(row), topic="config")


def _render_markdown(field_specs: list[FieldSpec]) -> str:
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
        default_value = _markdown_escape(_format_default(spec.default, spec.required))
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


def _markdown_escape(value: str | None) -> str:
    if not value:
        return ""
    return value.replace("|", "\\|")


__all__ = ["register"]
