from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from .common import CLIContext, CLIError
from .console import console

_COMPOSE_ACTION_TARGETS = {
    "up": "dev-up",
    "down": "dev-down",
    "logs": "dev-logs",
    "ps": "dev-ps",
}

_VAULT_ACTION_TARGETS = {
    "up": "vault-up",
    "down": "vault-down",
    "logs": "vault-logs",
    "verify": "verify-vault",
}

_DEPENDENCY_CHECKS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("Docker Engine", ("docker",), "Install Docker Desktop or the Docker Engine CLI."),
    (
        "Docker Compose v2",
        ("docker", "docker-compose"),
        "Install the Docker Compose plugin or legacy docker-compose binary.",
    ),
    ("Hatch", ("hatch",), "Install via `pipx install hatch` or `pip install --user hatch`."),
    ("Node.js", ("node",), "Install Node.js 20+ from nodejs.org or fnm/nvm."),
    ("pnpm", ("pnpm",), "Install via `npm install -g pnpm` or the pnpm installer."),
    ("Stripe CLI", ("stripe",), "Install from https://stripe.com/docs/stripe-cli."),
)

_VERSION_PROBES: dict[str, Callable[[tuple[str, ...]], tuple[str, ...]]] = {}


def _register_default_version_probes() -> None:
    def default(command: tuple[str, ...]) -> tuple[str, ...]:
        return (*command, "--version")

    def compose(command: tuple[str, ...]) -> tuple[str, ...]:
        if len(command) == 1:
            return (*command, "--version")
        return (*command, "version")

    for name, *_ in _DEPENDENCY_CHECKS:
        _VERSION_PROBES[name] = default
    _VERSION_PROBES["Docker Compose v2"] = compose


_register_default_version_probes()


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    infra_parser = subparsers.add_parser("infra", help="Provision local infrastructure helpers.")
    infra_subparsers = infra_parser.add_subparsers(dest="infra_command")

    compose_parser = infra_subparsers.add_parser(
        "compose",
        help="Manage the docker-compose stack (Postgres + Redis).",
    )
    compose_parser.add_argument(
        "action",
        choices=sorted(_COMPOSE_ACTION_TARGETS.keys()),
        help="Compose action to run via Makefile wrappers.",
    )
    compose_parser.set_defaults(handler=handle_compose)

    vault_parser = infra_subparsers.add_parser(
        "vault",
        help="Manage the local Vault dev signer container.",
    )
    vault_parser.add_argument(
        "action",
        choices=sorted(_VAULT_ACTION_TARGETS.keys()),
        help="Vault helper action to run via Make targets.",
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


@dataclass(slots=True)
class DependencyStatus:
    name: str
    binaries: tuple[str, ...]
    command: tuple[str, ...] | None
    hint: str
    version: str | None = None

    @property
    def status(self) -> str:
        return "ok" if self.command else "missing"

    @property
    def path(self) -> str | None:
        if not self.command:
            return None
        return self.command[0]

    @property
    def command_display(self) -> str:
        if not self.command:
            return ""
        return " ".join(self.command)


def handle_compose(args: argparse.Namespace, ctx: CLIContext) -> int:
    target = _COMPOSE_ACTION_TARGETS.get(args.action)
    if not target:  # pragma: no cover - argparse guards choices
        raise CLIError(f"Unknown compose action: {args.action}")
    _run_make(ctx, target)
    return 0


def handle_vault(args: argparse.Namespace, ctx: CLIContext) -> int:
    target = _VAULT_ACTION_TARGETS.get(args.action)
    if not target:  # pragma: no cover - argparse guards choices
        raise CLIError(f"Unknown vault action: {args.action}")
    _run_make(ctx, target)
    return 0


def handle_deps(args: argparse.Namespace, _ctx: CLIContext) -> int:
    statuses = list(collect_dependency_statuses())
    if args.format == "json":
        payload = [
            {
                "name": status.name,
                "status": status.status,
                "version": status.version or "",
                "path": status.path,
                "command": status.command,
                "hint": status.hint if status.status != "ok" else "",
            }
            for status in statuses
        ]
        json.dump(
            {
                "dependencies": payload,
                "missing": [status.name for status in statuses if status.status != "ok"],
                "ok": [status.name for status in statuses if status.status == "ok"],
            },
            console.stream,
            indent=2,
        )
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
        "For a machine-readable inventory, run `starter_cli config dump-schema --format json`.",
        topic="deps",
    )
    return 0


def collect_dependency_statuses() -> Iterable[DependencyStatus]:
    for name, binaries, hint in _DEPENDENCY_CHECKS:
        if name == "Docker Compose v2":
            command = _detect_compose_command()
        else:
            command = _first_existing_binary(binaries)
        version = _detect_version(name, command)
        yield DependencyStatus(
            name=name,
            binaries=binaries,
            command=command,
            hint=hint,
            version=version,
        )


def _first_existing_binary(candidates: Iterable[str]) -> tuple[str, ...] | None:
    for binary in candidates:
        path = shutil.which(binary)
        if path:
            return (path,)
    return None


def _run_make(ctx: CLIContext, target: str) -> None:
    cmd = ["make", target]
    console.info(f"$ {' '.join(cmd)}", topic="infra")
    subprocess.run(cmd, cwd=ctx.project_root, check=True)


def _detect_compose_command() -> tuple[str, ...] | None:
    legacy = shutil.which("docker-compose")
    if legacy:
        return (legacy,)
    docker = shutil.which("docker")
    if not docker:
        return None
    try:
        subprocess.run(
            [docker, "compose", "version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return (docker, "compose")


def _detect_version(name: str, command: tuple[str, ...] | None) -> str | None:
    if not command:
        return None
    probe = _VERSION_PROBES.get(name)
    if not probe:
        return None
    try:
        version_cmd = probe(command)
    except Exception:  # pragma: no cover - defensive
        return None
    try:
        result = subprocess.run(
            version_cmd,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    output = (result.stdout or result.stderr).strip()
    return output or None


__all__ = ["register", "collect_dependency_statuses", "DependencyStatus"]
