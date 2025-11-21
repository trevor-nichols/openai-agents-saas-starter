from __future__ import annotations

import argparse
import os
from collections.abc import Iterable
from pathlib import Path

from dotenv import dotenv_values

from starter_cli.core import CLIContext, CLIError


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
    command = list(args.exec_command)
    env_files = list(args.env_files)

    # argparse will happily consume everything into env_files (+) if users forget/remix the
    # separator. Recover by splitting on the first literal "--" when command is empty.
    if not command and "--" in env_files:
        dash_index = env_files.index("--")
        command = env_files[dash_index + 1 :]
        env_files = env_files[:dash_index]

    # Fallback: argparse drops the literal "--" for REMAINDER under subparsers.
    # When command is still empty, assume env files are the leading existing files
    # and the first non-file token starts the command.
    if not command:
        for idx, token in enumerate(env_files):
            if not Path(token).is_file() and "=" not in token:
                command = env_files[idx:]
                env_files = env_files[:idx]
                break

    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise CLIError("Command is required after env files (use -- to separate).")

    merged_env = os.environ.copy()
    merged_env.update(_merge_env(env_files))
    os.execvpe(command[0], command, merged_env)
    return 0  # never reached


def _merge_env(files: Iterable[str]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for path in files:
        merged.update(_load_env(path))
    return merged


def _load_env(path: str) -> dict[str, str]:
    file_path = Path(path)
    if not file_path.is_file():
        return {}
    values = dotenv_values(file_path)
    return {key: value for key, value in values.items() if value is not None}


__all__ = ["register"]
