from __future__ import annotations

import datetime
import os
import shutil
import subprocess
import threading
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from starter_cli.core import CLIContext
from starter_cli.core.constants import DEFAULT_COMPOSE_FILE
from starter_cli.ports.console import ConsolePort
from starter_cli.services.infra import ops_models
from starter_cli.services.infra.compose import detect_compose_command

DEFAULT_LINES = 200
SERVICE_CHOICES = ("all", "api", "frontend", "collector", "postgres", "redis")


@dataclass(slots=True)
class TailTarget:
    name: str
    command: list[str]
    cwd: Path


@dataclass(slots=True)
class TailStream:
    target: TailTarget
    process: subprocess.Popen[str]
    thread: threading.Thread


@dataclass(frozen=True, slots=True)
class ArchiveLogsConfig:
    days: int
    log_root: Path | None
    dry_run: bool


def resolve_tail_settings(lines: int | None, *, follow: bool, no_follow: bool) -> tuple[int, bool]:
    resolved_lines = DEFAULT_LINES if lines is None else max(lines, 1)
    explicit_lines = lines is not None

    if follow:
        resolved_follow = True
    elif no_follow:
        resolved_follow = False
    else:
        resolved_follow = not explicit_lines
    return resolved_lines, resolved_follow


def plan_targets(
    ctx: CLIContext,
    requested: Iterable[str],
    *,
    lines: int,
    follow: bool,
    errors_only: bool,
    console: ConsolePort,
    env: Mapping[str, str] | None = None,
) -> tuple[list[TailTarget], list[tuple[str, str]]]:
    settings = ctx.optional_settings()
    env_map = env or os.environ
    notes: list[tuple[str, str]] = []
    targets: list[TailTarget] = []

    def env_bool(key: str, default: bool = False) -> bool:
        raw = env_map.get(key)
        if raw is None and settings is not None:
            raw = str(getattr(settings, key.lower(), "")) or None
        if raw is None:
            return default
        return raw.lower() in {"1", "true", "yes", "on"}

    def env_value(key: str, default: str | None = None) -> str | None:
        value = env_map.get(key)
        if value is None and settings is not None:
            value = getattr(settings, key.lower(), None)
            if value is not None:
                value = str(value)
        return value or default

    log_root_raw = cast(
        str,
        env_value("LOG_ROOT", None) or str(ops_models.DEFAULT_LOG_ROOT),
    )
    base_root_raw = Path(log_root_raw).expanduser()
    base_root = base_root_raw if base_root_raw.is_absolute() else (ctx.project_root / base_root_raw)
    today_dir = datetime.date.today().isoformat()
    current_root = (base_root / "current").resolve() if (base_root / "current").exists() else None
    date_root = base_root / today_dir
    resolved_root = current_root if current_root and current_root.exists() else date_root

    normalized = normalize_services(
        requested,
        enable_collector=env_bool("ENABLE_OTEL_COLLECTOR"),
        console=console,
    )

    compose_cmd = detect_compose_command()
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
        sink_raw = env_value("LOGGING_SINKS") or "stdout"
        sinks = [part.strip().lower() for part in (sink_raw or "stdout").split(",") if part.strip()]
        sink_primary = sinks[0] if sinks else "stdout"
        sink_has_file = "file" in sinks

        resolved_sink = "file" if sink_has_file else sink_primary

        log_path = resolve_api_log_path(
            ctx,
            sink=resolved_sink,
            base_root=base_root,
            preferred_date_root=resolved_root if resolved_root.exists() else date_root,
            explicit_path=env_value("LOGGING_FILE_PATH"),
            errors_only=errors_only,
        )

        if log_path:
            cmd = ["tail"]
            if follow:
                cmd.append("-f")
            cmd.extend(["-n", str(lines), str(log_path)])
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


def resolve_api_log_path(
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


def normalize_services(
    requested: Iterable[str],
    *,
    enable_collector: bool,
    console: ConsolePort,
) -> set[str]:
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


def _stream_process(
    console: ConsolePort,
    *,
    target: TailTarget,
    process: subprocess.Popen[str],
    errors: list[str],
) -> None:
    with process:
        if process.stdout:
            for line in process.stdout:
                console.info(f"[{target.name}] {line.rstrip()}", topic="logs")
        code = process.wait()
        if code not in (0, None):
            errors.append(f"[{target.name}] exited with code {code}")


def stream_target(console: ConsolePort, target: TailTarget, errors: list[str]) -> None:
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

    _stream_process(console, target=target, process=proc, errors=errors)


def start_stream(
    console: ConsolePort,
    target: TailTarget,
    errors: list[str],
) -> TailStream | None:
    try:
        proc = subprocess.Popen(
            target.command,
            cwd=target.cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            start_new_session=True,
        )
    except FileNotFoundError as exc:  # missing binary
        errors.append(f"[{target.name}] command not found: {exc}")
        return None

    thread = threading.Thread(
        target=_stream_process,
        kwargs={"console": console, "target": target, "process": proc, "errors": errors},
        daemon=True,
    )
    thread.start()
    return TailStream(target=target, process=proc, thread=thread)


def stop_streams(streams: Iterable[TailStream]) -> None:
    for stream in streams:
        _terminate_process(stream.process)
        try:
            stream.thread.join(timeout=1.5)
        except RuntimeError:
            continue


def _terminate_process(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    try:
        proc.terminate()
    except Exception:
        return
    try:
        proc.wait(timeout=2)
    except Exception:
        try:
            proc.kill()
            proc.wait(timeout=2)
        except Exception:
            return


def archive_logs(ctx: CLIContext, config: ArchiveLogsConfig) -> int:
    console = ctx.console
    base_root = ops_models.resolve_log_root_override(
        ctx.project_root,
        os.environ,
        override=config.log_root,
    )

    days = max(config.days, 0)
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
        if config.dry_run:
            console.info(
                f"[dry-run] would archive {entry} -> {archive_path}", topic="logs"
            )
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


__all__ = [
    "ArchiveLogsConfig",
    "DEFAULT_LINES",
    "SERVICE_CHOICES",
    "TailStream",
    "TailTarget",
    "archive_logs",
    "normalize_services",
    "plan_targets",
    "resolve_api_log_path",
    "resolve_tail_settings",
    "start_stream",
    "stop_streams",
    "stream_target",
]
