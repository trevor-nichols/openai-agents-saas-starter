from __future__ import annotations

import argparse

from starter_cli.core import CLIContext
from starter_cli.workflows.home import HomeController


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "home",
        help="Interactive home hub showing stack status and shortcuts.",
    )
    parser.add_argument(
        "--no-tui",
        action="store_true",
        help="Disable the TUI and print a concise summary instead.",
    )
    parser.set_defaults(handler=_handle_home)


def _handle_home(args: argparse.Namespace, ctx: CLIContext) -> int:
    controller = HomeController(ctx)
    return controller.run(use_tui=not args.no_tui)


__all__ = ["register"]
