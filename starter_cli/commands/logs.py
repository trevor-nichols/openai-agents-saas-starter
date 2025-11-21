from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import threading
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIContext

DEFAULT_LINES = 200
SERVICE_CHOICES = ("all", "api", "frontend", "collector", "postgres", "redis")


@dataclass(slots=True)
class TailTarget:
    name: str
    command: list[str]
    cwd: Path


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "logs",
        help="Tail logs for backend, frontend ingest, and infra services.",
    )
    logs_subparsers = parser.add_subparsers(dest="logs_command")

    tail_parser = logs_subparsers.add_parser(
        "tail",
        help="Stream logs for selected services (api/frontend/collector/postgres/redis).",
    )
    tail_parser.add_argument(
        "--service",
        "-s",
        action="append",
        choices=SERVICE_CHOICES,
        help="Service(s) to tail. Defaults to all available.",
    )
    tail_parser.add_argument(
        "--lines",
        "-n",
        type=int,
        default=DEFAULT_LINES,
        help=f"Number of recent lines to show (default {DEFAULT_LINES}).",
    )
    tail_parser.add_argument(
        "--no-follow",
        action="store_true",
        help="Do not follow; exit after printing the last buffered lines.",
    )
    tail_parser.set_defaults(handler=_handle_tail)


def _handle_tail(args: argparse.Namespace, ctx: CLIContext) -> int:
    follow = not args.no_follow
    services = args.service or ["all"]

    targets, notes = _plan_targets(ctx, services, lines=max(args.lines, 1), follow=follow)

    for level, message in notes:
        if level == "warn":
            console.warn(message, topic="logs")
        else:
            console.info(message, topic="logs")

    if not targets:
        return 0

    errors: list[str] = []
    threads: list[threading.Thread] = []

    try:
        for target in targets:
            thread = threading.Thread(
                target=_stream_target,
                args=(target, errors),
                daemon=True,
            )
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        for target in targets:
            _terminate_processes_named(target.command[0])
    finally:
        for error in errors:
            console.warn(error, topic="logs")

    return 1 if errors else 0


def _plan_targets(
    ctx: CLIContext,
    requested: Iterable[str],
    *,
    lines: int,
    follow: bool,
) -> tuple[list[TailTarget], list[tuple[str, str]]]:
    settings = ctx.optional_settings()
    env = os.environ
    notes: list[tuple[str, str]] = []
    targets: list[TailTarget] = []

    def env_bool(key: str, default: bool = False) -> bool:
        raw = env.get(key)
        if raw is None and settings is not None:
            raw = str(getattr(settings, key.lower(), "")) or None
        if raw is None:
            return default
        return raw.lower() in {"1", "true", "yes", "on"}

    def env_value(key: str, default: str | None = None) -> str | None:
        value = env.get(key)
        if value is None and settings is not None:
            value = getattr(settings, key.lower(), None)
            if value is not None:
                value = str(value)
        return value or default

    normalized = _normalize_services(requested, enable_collector=env_bool("ENABLE_OTEL_COLLECTOR"))

    compose_cmd = _detect_compose_command()
    compose_services = {"postgres": "postgres", "redis": "redis", "collector": "otel-collector"}

    # Postgres / Redis / Collector via compose
    for svc in ("postgres", "redis", "collector"):
        if svc not in normalized:
            continue
        compose_service = compose_services[svc]
        if not compose_cmd:
            notes.append(("warn", "docker compose not found; skipping compose-managed services."))
            break
        cmd = [*compose_cmd, "logs", "--tail", str(lines)]
        if follow:
            cmd.append("-f")
        cmd.append(compose_service)
        targets.append(TailTarget(name=svc, command=cmd, cwd=ctx.project_root))

    # API log file (rotating file sink)
    if "api" in normalized:
        sink = (env_value("LOGGING_SINK", "stdout") or "stdout").lower()
        log_path_raw = env_value("LOGGING_FILE_PATH", "var/log/api-service.log")
        log_path = Path(log_path_raw) if log_path_raw else None

        if sink == "file" and log_path is not None:
            if not log_path.is_absolute():
                log_path = (ctx.project_root / log_path).resolve()
            if log_path.exists():
                cmd = ["tail", "-n", str(lines), str(log_path)]
                if follow:
                    cmd.insert(2, "-f")
                targets.append(TailTarget(name="api", command=cmd, cwd=ctx.project_root))
            else:
                message = (
                    "LOGGING_SINK=file but log path"
                    f" {log_path} does not exist; start the API once"
                    " or adjust LOGGING_FILE_PATH."
                )
                notes.append(("warn", message))
        else:
            message = (
                "API is not writing to a file sink. Run the API in another terminal"
                " or set LOGGING_SINK=file to enable tailing."
            )
            notes.append(("info", message))

    # Frontend guidance
    if "frontend" in normalized:
        ingest_enabled = env_bool("ENABLE_FRONTEND_LOG_INGEST", False)
        if ingest_enabled:
            message = (
                "Frontend logs flow into backend via /api/v1/logs."
                " Use --service api to view them (frontend.log event)."
            )
            notes.append(("info", message))
        else:
            message = (
                "Frontend runtime logs come from the Next.js dev server;"
                " run `pnpm dev --filter web-app` in another terminal to see them."
            )
            notes.append(("info", message))

    return targets, notes


def _normalize_services(requested: Iterable[str], *, enable_collector: bool) -> set[str]:
    requested_set = {svc.lower() for svc in requested}
    if "all" in requested_set:
        base = {"api", "frontend", "postgres", "redis"}
        if enable_collector:
            base.add("collector")
        return base
    normalized = {svc for svc in requested_set if svc in SERVICE_CHOICES}
    if "collector" in normalized and not enable_collector:
        console.warn("ENABLE_OTEL_COLLECTOR is false; skipping collector logs.", topic="logs")
        normalized.discard("collector")
    return normalized


def _stream_target(target: TailTarget, errors: list[str]) -> None:
    try:
        proc = subprocess.Popen(
            target.command,
            cwd=target.cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError as exc:  # missing binary
        errors.append(f"[{target.name}] command not found: {exc}")
        return

    with proc:
        if proc.stdout:
            for line in proc.stdout:
                console.info(f"[{target.name}] {line.rstrip()}", topic="logs")
        code = proc.wait()
        if code not in (0, None):
            errors.append(f"[{target.name}] exited with code {code}")


def _terminate_processes_named(binary: str) -> None:
    path = shutil.which(binary)
    if not path:
        return
    try:
        subprocess.run(
            ["pkill", "-f", shlex.quote(path)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def _detect_compose_command() -> list[str] | None:
    docker = shutil.which("docker")
    if docker:
        try:
            subprocess.run(
                [docker, "compose", "version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            return [docker, "compose"]
        except Exception:
            pass

    legacy = shutil.which("docker-compose")
    if legacy:
        return [legacy]

    return None


__all__ = ["register"]
