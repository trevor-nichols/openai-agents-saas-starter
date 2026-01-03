from __future__ import annotations

import argparse
import json
import subprocess
from collections.abc import Iterable
from pathlib import Path

from starter_contracts.infra.terraform_spec import TerraformProvider, get_provider_spec

from starter_console.adapters.env.files import EnvFile, aggregate_env_values
from starter_console.core import CLIContext, CLIError
from starter_console.ports.console import ConsolePort
from starter_console.services.infra import (
    COMPOSE_ACTION_TARGETS,
    VAULT_ACTION_TARGETS,
    collect_dependency_statuses,
    just_command,
    resolve_compose_target,
    resolve_vault_target,
)
from starter_console.services.infra.terraform_export import (
    TerraformExportError,
    TerraformExportFormat,
    TerraformExportMode,
    TerraformExportOptions,
    build_export,
)
from starter_console.workflows.setup import load_answers_files, merge_answer_overrides


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    infra_parser = subparsers.add_parser("infra", help="Provision local infrastructure helpers.")
    infra_subparsers = infra_parser.add_subparsers(dest="infra_command")

    compose_parser = infra_subparsers.add_parser(
        "compose",
        help="Manage the docker compose stack (Postgres + Redis).",
    )
    compose_parser.add_argument(
        "action",
        choices=sorted(COMPOSE_ACTION_TARGETS.keys()),
        help="Compose action to run via Just automation wrappers.",
    )
    compose_parser.set_defaults(handler=handle_compose)

    vault_parser = infra_subparsers.add_parser(
        "vault",
        help="Manage the local Vault dev signer container.",
    )
    vault_parser.add_argument(
        "action",
        choices=sorted(VAULT_ACTION_TARGETS.keys()),
        help="Vault helper action to run via Just recipes.",
    )
    vault_parser.set_defaults(handler=handle_vault)

    deps_parser = infra_subparsers.add_parser(
        "deps",
        help="Check for required local dependencies (Docker, Hatch, Node.js, pnpm).",
    )
    deps_parser.add_argument(
        "--format",
        choices={"table", "json"},
        default="table",
        help="Output dependency status as a table (default) or JSON list.",
    )
    deps_parser.set_defaults(handler=handle_deps)

    terraform_parser = infra_subparsers.add_parser(
        "terraform",
        help="Export Terraform inputs for cloud blueprints.",
    )
    terraform_subparsers = terraform_parser.add_subparsers(dest="terraform_command")

    terraform_export_parser = terraform_subparsers.add_parser(
        "export",
        help="Generate a tfvars file for a hosting provider.",
    )
    terraform_export_parser.add_argument(
        "--provider",
        choices=[provider.value for provider in TerraformProvider],
        required=True,
        help="Target Terraform blueprint (aws, azure, gcp).",
    )
    terraform_export_parser.add_argument(
        "--mode",
        choices=[mode.value for mode in TerraformExportMode],
        default=TerraformExportMode.TEMPLATE.value,
        help="template emits placeholders; filled requires all required values.",
    )
    terraform_export_parser.add_argument(
        "--format",
        choices=[fmt.value for fmt in TerraformExportFormat],
        default=TerraformExportFormat.HCL.value,
        help="Output format (hcl or json).",
    )
    terraform_export_parser.add_argument(
        "--output",
        metavar="PATH",
        help="Write output to PATH (defaults to var/infra/<provider>/terraform.tfvars).",
    )
    terraform_export_parser.add_argument(
        "--answers-file",
        action="append",
        metavar="PATH",
        help="Optional answers file (JSON) with key/value pairs (repeatable).",
    )
    terraform_export_parser.add_argument(
        "--var",
        action="append",
        metavar="KEY=VALUE",
        help="Override a Terraform input or env alias (repeatable).",
    )
    terraform_export_parser.add_argument(
        "--extra-var",
        action="append",
        metavar="KEY=VALUE",
        help="Pass through additional Terraform inputs not in the schema (repeatable).",
    )
    terraform_export_parser.add_argument(
        "--env-file",
        action="append",
        metavar="PATH",
        help="Env file to prefill values (repeatable). Defaults to local .env.local files.",
    )
    terraform_export_parser.add_argument(
        "--include-advanced",
        action="store_true",
        help="Include advanced tuning variables in the export.",
    )
    terraform_export_parser.add_argument(
        "--include-secrets",
        action="store_true",
        help="Write sensitive values into the export (default redacts).",
    )
    terraform_export_parser.add_argument(
        "--include-defaults",
        action="store_true",
        help="Include optional defaults even when not required.",
    )
    terraform_export_parser.set_defaults(handler=handle_terraform_export)


def handle_compose(args: argparse.Namespace, ctx: CLIContext) -> int:
    target = resolve_compose_target(args.action)
    _run_just(ctx, ctx.console, target)
    return 0


def handle_vault(args: argparse.Namespace, ctx: CLIContext) -> int:
    target = resolve_vault_target(args.action)
    _run_just(ctx, ctx.console, target)
    return 0


def handle_deps(args: argparse.Namespace, ctx: CLIContext) -> int:
    console = ctx.console
    statuses = list(collect_dependency_statuses())
    if args.format == "json":
        payload = [
            {
                "name": status.name,
                "status": status.status,
                "version": status.version or "",
                "path": status.path,
                "command": list(status.command) if status.command else None,
                "hint": status.hint if status.status != "ok" else "",
            }
            for status in statuses
        ]
        json.dump(payload, console.stream, indent=2)
        console.stream.write("\n")
        return 1 if any(status.status != "ok" for status in statuses) else 0

    console.info("Checking local prerequisites …", topic="deps")
    for status in statuses:
        if status.status == "ok":
            version = f" ({status.version})" if status.version else ""
            location = status.path or status.command_display
            console.success(f"{status.name}: {location}{version}", topic="deps")
        else:
            console.warn(f"{status.name}: missing. {status.hint}", topic="deps")
    console.info(
        "For a machine-readable inventory, run `starter-console config dump-schema --format json`.",
        topic="deps",
    )
    return 0


def handle_terraform_export(args: argparse.Namespace, ctx: CLIContext) -> int:
    provider = TerraformProvider(args.provider)
    spec = get_provider_spec(provider)

    answers = load_answers_files(args.answers_file or [])
    overrides = merge_answer_overrides({}, args.var or [])
    _ensure_known_overrides(spec, overrides)
    extra_vars = _parse_kv_args(args.extra_var or [])

    env_files = _resolve_env_files(ctx, args.env_file)
    env_values = _collect_env_aliases(spec, env_files)

    options = TerraformExportOptions(
        provider=provider,
        mode=TerraformExportMode(args.mode),
        format=TerraformExportFormat(args.format),
        include_advanced=bool(args.include_advanced),
        include_secrets=bool(args.include_secrets),
        include_defaults=bool(args.include_defaults),
    )
    try:
        result = build_export(
            options=options,
            overrides=overrides,
            answers=answers,
            env=env_values,
            extra_vars=extra_vars or None,
        )
    except TerraformExportError as exc:
        raise CLIError(str(exc)) from exc

    output_path = _resolve_output_path(ctx, provider, options.format, args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.render(format=options.format), encoding="utf-8")

    ctx.console.success(f"Wrote Terraform export to {output_path}", topic="infra")
    if result.missing_required or result.missing_requirements or result.failed_validations:
        _log_missing_requirements(
            ctx,
            result.missing_required,
            result.missing_requirements,
            result.failed_validations,
        )
    return 0


def _run_just(ctx: CLIContext, console: ConsolePort, target: str) -> None:
    cmd = just_command(target)
    console.info(f"$ {' '.join(cmd)}", topic="infra")
    subprocess.run(cmd, cwd=ctx.project_root, check=True)


def _resolve_output_path(
    ctx: CLIContext,
    provider: TerraformProvider,
    fmt: TerraformExportFormat,
    raw: str | None,
) -> Path:
    if raw:
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = ctx.project_root / path
        return path
    suffix = ".tfvars.json" if fmt == TerraformExportFormat.JSON else ".tfvars"
    return ctx.project_root / "var" / "infra" / provider.value / f"terraform{suffix}"


def _resolve_env_files(ctx: CLIContext, raw_paths: list[str] | None) -> list[EnvFile]:
    if raw_paths:
        resolved: list[Path] = []
        for raw in raw_paths:
            path = Path(raw).expanduser()
            if not path.is_absolute():
                path = ctx.project_root / path
            if not path.exists():
                raise CLIError(f"Env file not found: {path}")
            resolved.append(path)
        return [EnvFile(path) for path in resolved]

    candidates = [
        ctx.project_root / "apps" / "api-service" / ".env.local",
        ctx.project_root / "apps" / "web-app" / ".env.local",
    ]
    return [EnvFile(path) for path in candidates if path.exists()]


def _collect_env_aliases(spec, env_files: list[EnvFile]) -> dict[str, str]:
    keys = {
        alias
        for variable in spec.variables
        for alias in variable.env_aliases
    }
    if not keys:
        return {}
    aggregated = aggregate_env_values(env_files, keys)
    return {key: value for key, value in aggregated.items() if value is not None}


def _ensure_known_overrides(spec, overrides: dict[str, str]) -> None:
    known = {variable.name.lower() for variable in spec.variables}
    for variable in spec.variables:
        known.update(alias.lower() for alias in variable.env_aliases)
    for key in overrides.keys():
        if key.lower() in known:
            continue
        raise CLIError(
            f"Unknown Terraform input '{key}'. Use --extra-var for passthrough values."
        )


def _parse_kv_args(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw in values:
        if "=" not in raw:
            raise CLIError(f"Invalid value '{raw}'. Expected KEY=VALUE format.")
        key, value = raw.split("=", 1)
        parsed[key.strip()] = value
    return parsed


def _log_missing_requirements(
    ctx: CLIContext,
    missing_required: Iterable[str],
    missing_requirements: Iterable[str],
    failed_validations: Iterable[str],
) -> None:
    if missing_required:
        ctx.console.warn("Template export missing required values:", topic="infra")
        for name in sorted(missing_required):
            ctx.console.warn(f"- {name}", topic="infra")
    if missing_requirements:
        ctx.console.warn("Additional requirement hints:", topic="infra")
        for message in missing_requirements:
            ctx.console.warn(f"- {message}", topic="infra")
    if failed_validations:
        ctx.console.warn("Template export violates Terraform validations:", topic="infra")
        for message in failed_validations:
            ctx.console.warn(f"- {message}", topic="infra")


__all__ = ["register"]
