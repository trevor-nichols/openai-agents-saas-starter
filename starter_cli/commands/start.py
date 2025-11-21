from __future__ import annotations

import argparse

from starter_cli.core import CLIContext
from starter_cli.workflows.home.start import StartRunner

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
    parser.set_defaults(handler=_handle_start)


def _handle_start(args: argparse.Namespace, ctx: CLIContext) -> int:
    runner = StartRunner(
        ctx,
        target=args.target,
        timeout=float(args.timeout),
        open_browser=args.open_browser,
        skip_infra=args.skip_infra,
    )
    return runner.run()


__all__ = ["register"]
