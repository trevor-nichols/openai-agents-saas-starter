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
    raw = list(args.env_files)
    command = list(args.exec_command)

    if not command:
        env_files, command = _split_env_and_command(raw)
    else:
        env_files = raw

    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise CLIError("Command is required after env files (use -- to separate).")
    if command[0].startswith("-"):
        command = ["/bin/bash", *command]

    merged_env = os.environ.copy()
    merged_env.update(_merge_env(env_files))
    os.execvpe(command[0], command, merged_env)
    return 0  # never reached


def _merge_env(files: Iterable[str]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for token in files:
        if "=" in token and not token.startswith("-"):
            key, _, value = token.partition("=")
            if key:
                merged[key] = value
            continue
        merged.update(_load_env(token))
    return merged


def _split_env_and_command(tokens: list[str]) -> tuple[list[str], list[str]]:
    """Split env file tokens from command tokens.

    Rules:
    - If a literal '--' is present, everything after it is command.
    - Env files are tokens that look like .env files or KEY=VAL pairs.
    - Absolute paths that are executables (e.g., /bin/bash) are treated as commands.
    """
    if "--" in tokens:
        dash = tokens.index("--")
        return tokens[:dash], tokens[dash + 1 :]

    env_files: list[str] = []
    command: list[str] = []
    for idx, token in enumerate(tokens):
        if _is_env_token(token):
            env_files.append(token)
            continue
        command = tokens[idx:]
        break
    return env_files, command


def _is_env_token(token: str) -> bool:
    path = Path(token)
    looks_like_env_file = path.is_file() and (
        path.name.startswith(".env")
        or path.suffix in {".env", ".compose"}
        or path.name.endswith(".env.local")
    )
    inline_kv = "=" in token and not token.startswith("-")
    return looks_like_env_file or inline_kv


def _load_env(path: str) -> dict[str, str]:
    file_path = Path(path)
    if not file_path.is_file():
        return {}
    values = dotenv_values(file_path)
    return {key: value for key, value in values.items() if value is not None}


__all__ = ["register"]
