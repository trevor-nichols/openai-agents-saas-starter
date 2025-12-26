from __future__ import annotations

import argparse
from pathlib import Path

from starter_console.core import CLIContext
from starter_console.workflows.home.runtime import DEFAULT_PIDFILE_RELATIVE
from starter_console.workflows.home.start import StartRunner

TARGET_CHOICES = ("dev", "backend", "frontend")


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "start",
        help="Start local services with health checks (preview stub).",
    )
    parser.add_argument(
        "target",
        choices=TARGET_CHOICES,
        help="Which stack target to start (dev=all).",
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open frontend in the browser after start (opt-in).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Health wait timeout in seconds (default 120).",
    )
    parser.add_argument(
        "--skip-infra",
        action="store_true",
        help="Skip running just dev-up when target=dev.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--detached",
        action="store_true",
        help="Run services in background and return immediately (records PIDs).",
    )
    mode.add_argument(
        "--foreground",
        action="store_true",
        help="Keep processes attached (default).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing CLI-managed stack (stops tracked PIDs first).",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=None,
        help="Directory for detached-mode logs (default var/log).",
    )
    parser.add_argument(
        "--pidfile",
        type=Path,
        default=None,
        help=f"Path to stack state file (default {DEFAULT_PIDFILE_RELATIVE}).",
    )
    parser.set_defaults(handler=_handle_start)


def _handle_start(args: argparse.Namespace, ctx: CLIContext) -> int:
    runner = StartRunner(
        ctx,
        target=args.target,
        timeout=float(args.timeout),
        open_browser=args.open_browser,
        skip_infra=args.skip_infra,
        detach=args.detached,
        force=args.force,
        pidfile=args.pidfile,
        log_dir=args.log_dir,
    )
    return runner.run()


__all__ = ["register"]
