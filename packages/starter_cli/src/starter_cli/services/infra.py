from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable, Iterable
from dataclasses import dataclass

_COMPOSE_BINARIES = ("docker", "docker-compose")

_DEPENDENCY_CHECKS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("Docker Engine", ("docker",), "Install Docker Desktop or the Docker Engine CLI."),
    (
        "Docker Compose v2",
        _COMPOSE_BINARIES,
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
    return result.stdout.strip() or result.stderr.strip() or None


__all__ = ["DependencyStatus", "collect_dependency_statuses"]
