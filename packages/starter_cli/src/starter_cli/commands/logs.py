from __future__ import annotations

import argparse
from pathlib import Path

from starter_cli.core import CLIContext
from starter_cli.services.infra import logs_ops

ArchiveLogsConfig = logs_ops.ArchiveLogsConfig
SERVICE_CHOICES = logs_ops.SERVICE_CHOICES
archive_logs = logs_ops.archive_logs
plan_targets = logs_ops.plan_targets
resolve_tail_settings = logs_ops.resolve_tail_settings
start_stream = logs_ops.start_stream
stop_streams = logs_ops.stop_streams


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
        default=None,
        help=(
            "Number of recent lines to show. When set, the command exits after printing "
            "the lines unless --follow is also supplied."
        ),
    )
    follow_group = tail_parser.add_mutually_exclusive_group()
    follow_group.add_argument(
        "--follow",
        action="store_true",
        help="Always follow log updates (even when --lines is provided).",
    )
    follow_group.add_argument(
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
    console = ctx.console
    lines, follow = resolve_tail_settings(args.lines, follow=args.follow, no_follow=args.no_follow)
    services = args.service or ["all"]

    targets, notes = plan_targets(
        ctx,
        services,
        lines=lines,
        follow=follow,
        errors_only=args.errors,
        console=console,
    )

    for level, message in notes:
        if level == "warn":
            console.warn(message, topic="logs")
        else:
            console.info(message, topic="logs")

    if not targets:
        return 0

    errors: list[str] = []
    streams: list[logs_ops.TailStream] = []

    try:
        for target in targets:
            stream = start_stream(console, target, errors)
            if stream is not None:
                streams.append(stream)

        for stream in streams:
            stream.thread.join()
    except KeyboardInterrupt:
        stop_streams(streams)
    finally:
        for error in errors:
            console.warn(error, topic="logs")

    return 1 if errors else 0


def _handle_archive(args: argparse.Namespace, ctx: CLIContext) -> int:
    config = ArchiveLogsConfig(
        days=args.days,
        log_root=args.log_root,
        dry_run=args.dry_run,
    )
    return archive_logs(ctx, config)


__all__ = ["register"]
