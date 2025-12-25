from __future__ import annotations

import argparse
import json
from pathlib import Path

from starter_contracts.config import get_settings_class

from starter_console.core import CLIContext
from starter_console.ports.console import ConsolePort
from starter_console.services.config.inventory import (
    FieldSpec,
    collect_field_specs,
    format_default,
    render_markdown,
)


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
        default="docs/trackers/CONSOLE_ENV_INVENTORY.md",
        help=(
            "Destination path for the Markdown inventory "
            "(defaults to docs/trackers/CONSOLE_ENV_INVENTORY.md)."
        ),
    )
    inventory_parser.set_defaults(handler=handle_write_inventory)


def handle_dump_schema(args: argparse.Namespace, ctx: CLIContext) -> int:
    console = ctx.console
    settings_cls = get_settings_class()

    field_specs = collect_field_specs(settings_cls)
    if args.format == "json":
        json_payload = [spec.to_dict() for spec in field_specs]
        json.dump(json_payload, console.stream, indent=2)
        console.stream.write("\n")
        return 0

    _render_table(console, field_specs)
    return 0


def handle_write_inventory(args: argparse.Namespace, ctx: CLIContext) -> int:
    console = ctx.console
    field_specs = collect_field_specs(get_settings_class())
    destination = Path(args.path).expanduser().resolve()
    body = render_markdown(field_specs)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(body, encoding="utf-8")
    console.success(f"Environment inventory written to {destination}", topic="config")
    return 0


def _render_table(console: ConsolePort, field_specs: list[FieldSpec]) -> None:
    rows = [
        (
            spec.env_var,
            spec.type_hint,
            format_default(spec.default, spec.required),
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


__all__ = ["register"]
