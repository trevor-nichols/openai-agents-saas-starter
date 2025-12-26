"""Starter Console application entrypoint."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path

from .commands import register_all
from .container import ApplicationContainer, build_container
from .core import CLIContext, CLIError
from .core.context import resolve_env_files, should_skip_env_loading
from .observability import configure_console_logging, configure_textual_logging

Handler = Callable[[argparse.Namespace, CLIContext], int]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="starter-console",
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
            "Skip loading default env files (.env.compose, apps/api-service/.env, "
            "apps/api-service/.env.local). Explicit --env-file values still load."
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
) -> tuple[Path, ...]:
    custom_envs = container.iter_env_files(args.env_files or [])
    return resolve_env_files(custom_envs, skip_defaults=False)


def _load_environment(
    container: ApplicationContainer,
    args: argparse.Namespace,
) -> CLIContext:
    skip_env = args.skip_env or should_skip_env_loading()
    env_files = _resolve_env_files(container, args)
    ctx = container.create_context(
        env_files=env_files,
        skip_env=skip_env,
        quiet_env=args.quiet_env,
    )
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
        ctx = app_container.create_context(
            env_files=(),
            skip_env=True,
            quiet_env=args.quiet_env,
        )
    else:
        ctx = _load_environment(app_container, args)

    configure_console_logging(ctx)
    handler: Handler | None = getattr(args, "handler", None)
    if handler is None:
        return _launch_tui(ctx, initial_screen="home")

    try:
        return handler(args, ctx)
    except CLIError as exc:
        ctx.console.error(str(exc))
        return 1


def _launch_tui(ctx: CLIContext, *, initial_screen: str) -> int:
    configure_textual_logging(ctx)
    try:
        from starter_console.ui import StarterTUI

        StarterTUI(ctx, initial_screen=initial_screen).run()
        return 0
    except KeyboardInterrupt:
        ctx.console.warn("Interrupted. Goodbye!", topic="tui")
        return 130


__all__ = ["build_parser", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
