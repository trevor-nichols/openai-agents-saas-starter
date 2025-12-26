from __future__ import annotations

import argparse
import json
import subprocess

from starter_console.core import CLIContext
from starter_console.ports.console import ConsolePort
from starter_console.services.infra import (
    COMPOSE_ACTION_TARGETS,
    VAULT_ACTION_TARGETS,
    collect_dependency_statuses,
    just_command,
    resolve_compose_target,
    resolve_vault_target,
)


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


def _run_just(ctx: CLIContext, console: ConsolePort, target: str) -> None:
    cmd = just_command(target)
    console.info(f"$ {' '.join(cmd)}", topic="infra")
    subprocess.run(cmd, cwd=ctx.project_root, check=True)


__all__ = ["register"]
