from __future__ import annotations

import argparse
import datetime
import os
import shlex
import shutil
import subprocess
import threading
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIContext
from starter_cli.core.constants import DEFAULT_COMPOSE_FILE

DEFAULT_LINES = 200
SERVICE_CHOICES = ("all", "api", "frontend", "collector", "postgres", "redis")
DEFAULT_LOG_ROOT = Path("var/log")


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

    archive_parser = logs_subparsers.add_parser(
        "archive",
        help="Archive and optionally prune dated log directories.",
    )
    archive_parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Archive/prune logs older than this many days (default 7).",
    )
    archive_parser.add_argument(
        "--log-root",
        type=Path,
        default=None,
        help="Override log root (defaults to LOG_ROOT or var/log).",
    )
    archive_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be archived/pruned without changing files.",
    )
    archive_parser.set_defaults(handler=_handle_archive)

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
    tail_parser.add_argument(
        "--errors",
        action="store_true",
        help="Tail error logs instead of all logs when available.",
    )
    tail_parser.set_defaults(handler=_handle_tail)


def _handle_tail(args: argparse.Namespace, ctx: CLIContext) -> int:
    follow = not args.no_follow
    services = args.service or ["all"]

    targets, notes = _plan_targets(
        ctx, services, lines=max(args.lines, 1), follow=follow, errors_only=args.errors
    )

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


def _handle_archive(args: argparse.Namespace, ctx: CLIContext) -> int:
    base_root_raw = (args.log_root or Path(os.getenv("LOG_ROOT", DEFAULT_LOG_ROOT))).expanduser()
    base_root = (
        base_root_raw
        if base_root_raw.is_absolute()
        else (ctx.project_root / base_root_raw).resolve()
    )

    days = max(args.days, 0)
    cutoff = datetime.date.today() - datetime.timedelta(days=days)

    if not base_root.exists():
        console.info(f"No log root at {base_root}; nothing to archive.", topic="logs")
        return 0

    archived = 0
    for entry in sorted(base_root.iterdir()):
        if entry.name == "current" or not entry.is_dir():
            continue
        try:
            entry_date = datetime.date.fromisoformat(entry.name)
        except ValueError:
            continue
        if entry_date >= cutoff:
            continue

        archive_path = base_root / f"{entry.name}.zip"
        if args.dry_run:
            console.info(f"[dry-run] would archive {entry} -> {archive_path}", topic="logs")
            archived += 1
            continue

        try:
            shutil.make_archive(str(archive_path.with_suffix("")), "zip", base_root, entry.name)
            shutil.rmtree(entry, ignore_errors=True)
            console.info(f"Archived {entry} -> {archive_path.name}", topic="logs")
            archived += 1
        except Exception as exc:  # pragma: no cover - defensive
            console.warn(f"Failed to archive {entry}: {exc}", topic="logs")

    if archived == 0:
        console.info("No dated log directories matched archive criteria.", topic="logs")
    return 0


def _plan_targets(
    ctx: CLIContext,
    requested: Iterable[str],
    *,
    lines: int,
    follow: bool,
    errors_only: bool,
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

    log_root_raw = cast(str, env_value("LOG_ROOT", None) or str(DEFAULT_LOG_ROOT))
    base_root_raw = Path(log_root_raw).expanduser()
    base_root = base_root_raw if base_root_raw.is_absolute() else (ctx.project_root / base_root_raw)
    today_dir = datetime.date.today().isoformat()
    current_root = (base_root / "current").resolve() if (base_root / "current").exists() else None
    date_root = base_root / today_dir
    resolved_root = current_root if current_root and current_root.exists() else date_root

    normalized = _normalize_services(requested, enable_collector=env_bool("ENABLE_OTEL_COLLECTOR"))

    compose_cmd = _detect_compose_command()
    compose_file = DEFAULT_COMPOSE_FILE
    if compose_cmd and not compose_file.exists():
        notes.append(
            ("warn", f"Compose file not found at {compose_file}; skipping compose services.")
        )
        compose_cmd = None
    compose_services = {"postgres": "postgres", "redis": "redis", "collector": "otel-collector"}

    # Postgres / Redis / Collector via compose
    for svc in ("postgres", "redis", "collector"):
        if svc not in normalized:
            continue
        compose_service = compose_services[svc]
        if not compose_cmd:
            notes.append(("warn", "docker compose not found; skipping compose-managed services."))
            break
        cmd = [*compose_cmd, "-f", str(compose_file), "logs", "--tail", str(lines)]
        if follow:
            cmd.append("-f")
        cmd.append(compose_service)
        targets.append(TailTarget(name=svc, command=cmd, cwd=ctx.project_root))

    # API log file (rotating file sink)
    if "api" in normalized:
        sink_raw = env_value("LOGGING_SINKS") or env_value("LOGGING_SINK", "stdout")
        sinks = [part.strip().lower() for part in (sink_raw or "stdout").split(",") if part.strip()]
        sink_primary = sinks[0] if sinks else "stdout"
        sink_has_file = "file" in sinks

        resolved_sink = "file" if sink_has_file else sink_primary

        log_path = _resolve_api_log_path(
            ctx,
            sink=resolved_sink,
            base_root=base_root,
            preferred_date_root=resolved_root if resolved_root.exists() else date_root,
            explicit_path=env_value("LOGGING_FILE_PATH"),
            errors_only=errors_only,
        )

        if log_path:
            cmd = ["tail", "-n", str(lines), str(log_path)]
            if follow:
                cmd.insert(2, "-f")
            targets.append(TailTarget(name="api", command=cmd, cwd=ctx.project_root))
        else:
            if sink_has_file or resolved_sink == "file":
                message = (
                    "File sink enabled but no log file found yet; start the API"
                    " or check LOG_ROOT/LOGGING_FILE_PATH."
                )
                notes.append(("warn", message))
            elif errors_only:
                notes.append(
                    ("info", "Error log not found; try without --errors or enable file sink.")
                )
            else:
                message = (
                    "API is not writing to a file sink. Run the API in another terminal"
                    " or set LOGGING_SINKS to include 'file' to enable tailing."
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


def _resolve_api_log_path(
    ctx: CLIContext,
    *,
    sink: str,
    base_root: Path,
    preferred_date_root: Path | None,
    explicit_path: str | None,
    errors_only: bool,
) -> Path | None:
    # 1) Respect explicit LOGGING_FILE_PATH if set
    if explicit_path:
        candidate = Path(explicit_path)
        if not candidate.is_absolute():
            candidate = (ctx.project_root / candidate).resolve()
        if errors_only:
            error_candidate = candidate.parent / "error.log"
            if error_candidate.exists():
                return error_candidate
        if candidate.exists():
            return candidate

    # 2) Dated layout: base_root/(current|YYYY-MM-DD)/api/(error|all).log
    candidate_name = "error.log" if errors_only else "all.log"
    if preferred_date_root and preferred_date_root.exists():
        candidate = preferred_date_root / "api" / candidate_name
        if candidate.exists():
            return candidate

    if not base_root.exists():
        return None

    dated_dirs = sorted(
        [p for p in base_root.iterdir() if p.is_dir() and p.name != "current"],
        reverse=True,
    )
    for root in dated_dirs:
        path = root / "api" / candidate_name
        if path.exists():
            return path

    return None


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
