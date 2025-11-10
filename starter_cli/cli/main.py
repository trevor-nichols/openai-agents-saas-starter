from __future__ import annotations

import argparse
import os
from collections.abc import Callable, Sequence

from . import auth_commands, setup_commands, stripe_commands
from .common import (
    DEFAULT_ENV_FILES,
    CLIContext,
    CLIError,
    build_context,
    iter_env_files,
)
from .console import console

Handler = Callable[[argparse.Namespace, CLIContext], int]
_SKIP_ENV_FLAG = "STARTER_CLI_SKIP_ENV"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anything-agents",
        description="Operator tooling for the OpenAI Agents starter stack.",
    )
    parser.add_argument(
        "--env-file",
        action="append",
        dest="env_files",
        default=[],
        help="Additional env file(s) to load before running the command.",
    )
    parser.add_argument(
        "--skip-env",
        action="store_true",
        help="Skip loading default env files (.env.local, .env, .env.compose).",
    )
    parser.add_argument(
        "--quiet-env",
        action="store_true",
        help="Suppress informational logs when loading env files.",
    )

    subparsers = parser.add_subparsers(dest="command")
    auth_commands.register(subparsers)
    stripe_commands.register(subparsers)
    setup_commands.register(subparsers)
    return parser


def _load_environment(args: argparse.Namespace) -> CLIContext:
    custom_envs = iter_env_files(args.env_files or [])
    skip_env = args.skip_env or os.getenv(_SKIP_ENV_FLAG, "false").lower() in {
        "1",
        "true",
        "yes",
    }

    env_files: Sequence[str] | Sequence[os.PathLike[str]] | None
    if skip_env:
        env_files = custom_envs if custom_envs else None
    else:
        default_paths = list(DEFAULT_ENV_FILES)
        if custom_envs:
            default_paths.extend(custom_envs)
        env_files = default_paths

    ctx = build_context(env_files=env_files)
    should_load_env = env_files is not None
    if should_load_env:
        ctx.load_environment(verbose=not args.quiet_env)
    return ctx


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    ctx = _load_environment(args)

    handler: Handler | None = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0

    try:
        return handler(args, ctx)
    except CLIError as exc:
        console.error(str(exc))
        return 1


__all__ = ["main", "build_parser"]
