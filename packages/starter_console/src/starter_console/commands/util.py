from __future__ import annotations

import argparse
import os

from starter_console.core import CLIContext
from starter_console.services.infra.run_with_env import prepare_run_with_env


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    util_parser = subparsers.add_parser("util", help="Utility helpers.")
    util_subparsers = util_parser.add_subparsers(dest="util_command")

    run_parser = util_subparsers.add_parser(
        "run-with-env",
        help="Merge one or more env files, then exec the provided command.",
    )
    run_parser.add_argument(
        "env_files",
        nargs="+",
        help="Env files to merge (later files win on conflicts).",
    )
    run_parser.add_argument(
        "exec_command",
        nargs=argparse.REMAINDER,
        help="Command to execute; add -- to stop parsing (e.g., run-with-env .env -- echo hi).",
    )
    run_parser.set_defaults(handler=handle_run_with_env)


def handle_run_with_env(args: argparse.Namespace, _ctx: CLIContext) -> int:
    plan = prepare_run_with_env(args.env_files, args.exec_command)
    os.execvpe(plan.command[0], plan.command, plan.merged_env)
    return 0  # never reached


__all__ = ["register"]
