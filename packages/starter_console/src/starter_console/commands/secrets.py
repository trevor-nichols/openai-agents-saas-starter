from __future__ import annotations

import argparse

from starter_contracts.secrets.models import SecretsProviderLiteral

from starter_console.core import CLIContext
from starter_console.services.secrets.onboard import SecretsOnboardConfig, run_secrets_onboard


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    secrets_parser = subparsers.add_parser("secrets", help="Secrets provider workflows.")
    secrets_subparsers = secrets_parser.add_subparsers(dest="secrets_command")

    onboard_parser = secrets_subparsers.add_parser(
        "onboard",
        help="Guided setup for the secrets/signing provider.",
    )
    onboard_parser.add_argument(
        "--provider",
        choices=[choice.value for choice in SecretsProviderLiteral],
        help="Secrets provider to configure (defaults to interactive menu).",
    )
    onboard_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Disable prompts and rely entirely on --answers-file/--var.",
    )
    onboard_parser.add_argument(
        "--answers-file",
        action="append",
        default=[],
        help="JSON file containing KEY: value pairs for prompts (repeatable).",
    )
    onboard_parser.add_argument(
        "--var",
        action="append",
        default=[],
        help="Override a prompt answer, e.g. --var VAULT_ADDR=https://vault.local",
    )
    onboard_parser.add_argument(
        "--skip-automation",
        action="store_true",
        dest="skip_automation",
        help="Skip invoking local automation recipes (e.g., just dev-up) even if offered.",
    )
    onboard_parser.add_argument(
        "--skip-make",
        action="store_true",
        dest="skip_automation",
        help=argparse.SUPPRESS,
    )
    onboard_parser.set_defaults(handler=handle_onboard)


def handle_onboard(args: argparse.Namespace, ctx: CLIContext) -> int:
    config = SecretsOnboardConfig(
        provider=args.provider,
        non_interactive=args.non_interactive,
        answers_files=args.answers_file or (),
        overrides=args.var or (),
        skip_automation=args.skip_automation,
    )
    run_secrets_onboard(ctx, config)
    return 0


__all__ = ["register"]
