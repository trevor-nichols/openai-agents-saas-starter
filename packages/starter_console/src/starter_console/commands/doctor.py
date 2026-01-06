from __future__ import annotations

import argparse
from pathlib import Path

from starter_console.core import CLIContext
from starter_console.core.profiles import load_profile_registry, select_profile
from starter_console.workflows.home.doctor import DoctorRunner


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "doctor",
        help="Run consolidated readiness checks for demo or remote profiles.",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Deployment profile (defaults to auto-detect).",
    )
    parser.add_argument(
        "--profiles-path",
        metavar="PATH",
        help="Optional profile config file path (defaults to config/starter-console.profile.yaml).",
    )
    parser.add_argument(
        "--json",
        metavar="PATH",
        type=Path,
        help="Write machine-friendly results to PATH.",
    )
    parser.add_argument(
        "--markdown",
        metavar="PATH",
        type=Path,
        help="Write a Markdown summary to PATH.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (useful outside demo profile).",
    )
    parser.set_defaults(handler=_handle_doctor)


def _handle_doctor(args: argparse.Namespace, ctx: CLIContext) -> int:
    registry = load_profile_registry(
        project_root=ctx.project_root,
        override_path=Path(args.profiles_path).expanduser()
        if args.profiles_path
        else None,
    )
    selection = select_profile(registry, explicit=args.profile)
    runner = DoctorRunner(ctx, profile=selection.profile.profile_id, strict=args.strict)
    return runner.run(json_path=args.json, markdown_path=args.markdown)


__all__ = ["register"]
