from __future__ import annotations

import argparse

from starter_console.core import CLIContext
from starter_console.services.infra.release_db import DatabaseReleaseConfig, DatabaseReleaseWorkflow


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    release_parser = subparsers.add_parser("release", help="Release automation workflows.")
    release_subparsers = release_parser.add_subparsers(dest="release_command")

    db_parser = release_subparsers.add_parser(
        "db",
        help="Run migrations, Stripe seeding, and billing plan verification.",
    )
    db_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help=(
            "Fail instead of prompting for inputs "
            "(requires explicit Stripe params or --skip-stripe)."
        ),
    )
    db_parser.add_argument(
        "--skip-stripe",
        action="store_true",
        help="Skip the embedded Stripe setup flow (attach manual evidence separately).",
    )
    db_parser.add_argument(
        "--skip-db-checks",
        action="store_true",
        help="Skip billing plan verification queries.",
    )
    db_parser.add_argument(
        "--summary-path",
        help=(
            "Optional path for the JSON summary artifact "
            "(defaults to var/reports/db-release-<timestamp>.json)."
        ),
    )
    db_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the JSON summary to stdout after writing the artifact.",
    )
    db_parser.add_argument(
        "--plan",
        action="append",
        metavar="CODE=CENTS",
        help=(
            "Override Stripe plan amount when --non-interactive is used "
            "(forwarded to stripe setup)."
        ),
    )
    db_parser.set_defaults(handler=handle_db_release)


def handle_db_release(args: argparse.Namespace, ctx: CLIContext) -> int:
    config = DatabaseReleaseConfig(
        non_interactive=args.non_interactive,
        skip_stripe=args.skip_stripe,
        skip_db_checks=args.skip_db_checks,
        summary_path=args.summary_path,
        plan_overrides=args.plan or None,
        json_output=args.json,
    )
    workflow = DatabaseReleaseWorkflow(ctx=ctx, config=config)
    return workflow.run()


__all__ = ["register", "DatabaseReleaseConfig", "DatabaseReleaseWorkflow"]
