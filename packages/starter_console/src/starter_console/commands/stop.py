from __future__ import annotations

import argparse
from pathlib import Path

from starter_console.core import CLIContext
from starter_console.services.infra.stack_ops import stop_stack
from starter_console.workflows.home.runtime import DEFAULT_PIDFILE_RELATIVE


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "stop",
        help="Stop services started by `start --detached` and clear tracked state.",
    )
    parser.add_argument(
        "--pidfile",
        type=Path,
        default=None,
        help=f"Path to stack state file (default {DEFAULT_PIDFILE_RELATIVE}).",
    )
    parser.set_defaults(handler=_handle_stop)


def _handle_stop(args: argparse.Namespace, ctx: CLIContext) -> int:
    stop_stack(ctx, pidfile=args.pidfile)
    return 0


__all__ = ["register"]
