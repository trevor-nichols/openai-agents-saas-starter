"""Starter CLI application entrypoint."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from pathlib import Path

from .commands import register_all
from .container import ApplicationContainer, build_container
from .core import CLIContext, CLIError
from .core.constants import DEFAULT_ENV_FILES
from .core.context import should_skip_env_loading

Handler = Callable[[argparse.Namespace, CLIContext], int]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="starter-cli",
        description="Operator tooling for the OpenAI Agents SaaS starter stack.",
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
        help=(
            "Skip loading default env files (.env.compose, apps/api-service/.env.local, "
            "apps/api-service/.env, .env)."
        ),
    )
    parser.add_argument(
        "--quiet-env",
        action="store_true",
        help="Suppress informational logs when loading env files.",
    )
    subparsers = parser.add_subparsers(dest="command")
    register_all(subparsers)
    return parser


def _resolve_env_files(
    container: ApplicationContainer, args: argparse.Namespace
) -> Sequence[Path] | None:
    custom_envs = container.iter_env_files(args.env_files or [])
    skip_env = args.skip_env or should_skip_env_loading()

    if skip_env:
        return tuple(custom_envs) if custom_envs else None

    default_paths = list(DEFAULT_ENV_FILES)
    if custom_envs:
        default_paths.extend(custom_envs)
    return tuple(dict.fromkeys(default_paths))


def _load_environment(
    container: ApplicationContainer,
    args: argparse.Namespace,
) -> CLIContext:
    env_files = _resolve_env_files(container, args)
    ctx = container.create_context(env_files=env_files)
    if env_files is not None:
        container.load_environment(ctx, verbose=not args.quiet_env)
    return ctx


def main(argv: list[str] | None = None, *, container: ApplicationContainer | None = None) -> int:
    app_container = container or build_container()
    parser = build_parser()
    args = parser.parse_args(argv)
    if (
        getattr(args, "command", None) == "util"
        and getattr(args, "util_command", None) == "run-with-env"
    ):
        # run-with-env manages its own env merging; avoid double-loading via CLI.
        ctx = app_container.create_context(env_files=None)
    else:
        ctx = _load_environment(app_container, args)

    handler: Handler | None = getattr(args, "handler", None)
    if handler is None:
        return _launch_tui(ctx, initial_screen="home")

    try:
        return handler(args, ctx)
    except CLIError as exc:
        ctx.console.error(str(exc))
        return 1


def _launch_tui(ctx: CLIContext, *, initial_screen: str) -> int:
    try:
        from starter_cli.ui import StarterTUI

        StarterTUI(ctx, initial_screen=initial_screen).run()
        return 0
    except KeyboardInterrupt:
        ctx.console.warn("Interrupted. Goodbye!", topic="tui")
        return 130


__all__ = ["build_parser", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
