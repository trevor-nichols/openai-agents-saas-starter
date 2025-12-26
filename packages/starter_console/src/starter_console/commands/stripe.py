from __future__ import annotations

import argparse

from starter_console.core import CLIContext
from starter_console.workflows.stripe import (
    DEFAULT_WEBHOOK_FORWARD_URL,
    DISPATCH_STATUS_CHOICES,
    DispatchListConfig,
    DispatchReplayConfig,
    StripeSetupConfig,
    WebhookSecretConfig,
    run_dispatch_list,
    run_dispatch_replay,
    run_dispatch_validate_fixtures,
    run_stripe_setup,
    run_webhook_secret,
)


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    stripe_parser = subparsers.add_parser("stripe", help="Stripe provisioning helpers.")
    stripe_subparsers = stripe_parser.add_subparsers(dest="stripe_command")

    setup_parser = stripe_subparsers.add_parser(
        "setup",
        help="Interactive onboarding flow for billing assets and secrets.",
    )
    setup_parser.add_argument(
        "--currency",
        default="usd",
        help="Currency for plan provisioning (default: usd).",
    )
    setup_parser.add_argument(
        "--trial-days",
        type=int,
        default=7,
        help="Trial period in days for generated prices.",
    )
    setup_parser.add_argument(
        "--secret-key",
        help="Stripe secret key (sk_live_...). Required for --non-interactive.",
    )
    setup_parser.add_argument(
        "--webhook-secret",
        help="Stripe webhook signing secret. Required for --non-interactive.",
    )
    setup_parser.add_argument(
        "--auto-webhook-secret",
        action="store_true",
        help="Use Stripe CLI to generate a webhook signing secret (interactive only).",
    )
    setup_parser.add_argument(
        "--webhook-forward-url",
        default=DEFAULT_WEBHOOK_FORWARD_URL,
        help=(
            "Forwarding URL passed to `stripe listen --forward-to` "
            "when generating webhook secrets."
        ),
    )
    setup_parser.add_argument(
        "--plan",
        action="append",
        metavar="CODE=CENTS",
        help="Override plan pricing (e.g., starter=2500).",
    )
    setup_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Disable prompts and rely entirely on provided flags.",
    )
    setup_parser.add_argument(
        "--skip-postgres-check",
        action="store_true",
        help="Skip the optional Postgres helper/test.",
    )
    setup_parser.add_argument(
        "--skip-stripe-cli",
        action="store_true",
        help="Skip Stripe CLI verification (use when running in CI).",
    )
    setup_parser.set_defaults(handler=handle_stripe_setup)

    webhook_parser = stripe_subparsers.add_parser(
        "webhook-secret",
        help="Capture a Stripe webhook signing secret via Stripe CLI.",
    )
    webhook_parser.add_argument(
        "--forward-url",
        default=DEFAULT_WEBHOOK_FORWARD_URL,
        help="Forwarding URL passed to Stripe CLI (default: local FastAPI webhook endpoint).",
    )
    webhook_parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print the secret without writing apps/api-service/.env.local.",
    )
    webhook_parser.add_argument(
        "--skip-stripe-cli",
        action="store_true",
        help="Skip Stripe CLI verification (assumes the CLI is installed and authenticated).",
    )
    webhook_parser.set_defaults(handler=handle_webhook_secret)

    dispatch_parser = stripe_subparsers.add_parser(
        "dispatches",
        help="Inspect and replay stored Stripe webhook dispatches.",
    )
    dispatch_subparsers = dispatch_parser.add_subparsers(dest="dispatch_command")

    dispatch_list = dispatch_subparsers.add_parser(
        "list",
        help="List stored Stripe dispatches.",
    )
    dispatch_list.add_argument(
        "--status",
        choices=[*DISPATCH_STATUS_CHOICES, "all"],
        default="failed",
        help="Filter by status (default: failed). Use 'all' to show every status.",
    )
    dispatch_list.add_argument(
        "--handler",
        default="billing_sync",
        help="Handler name to filter (default: billing_sync).",
    )
    dispatch_list.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum rows to return (default: 20).",
    )
    dispatch_list.add_argument(
        "--page",
        type=int,
        default=1,
        help="Page number (1-indexed).",
    )
    dispatch_list.set_defaults(handler=handle_dispatch_list)

    dispatch_replay = dispatch_subparsers.add_parser(
        "replay",
        help="Replay stored dispatches through the dispatcher.",
    )
    dispatch_replay.add_argument(
        "--dispatch-id",
        action="append",
        help="Dispatch UUID(s) to replay.",
    )
    dispatch_replay.add_argument(
        "--event-id",
        action="append",
        help="Replay dispatches derived from Stripe event IDs.",
    )
    dispatch_replay.add_argument(
        "--status",
        choices=DISPATCH_STATUS_CHOICES,
        help="Replay all dispatches with the given status (respects --limit).",
    )
    dispatch_replay.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Limit when replaying by status (default: 5).",
    )
    dispatch_replay.add_argument(
        "--handler",
        default="billing_sync",
        help="Handler name to target (default: billing_sync).",
    )
    dispatch_replay.add_argument(
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt.",
    )
    dispatch_replay.set_defaults(handler=handle_dispatch_replay)

    fixtures_parser = dispatch_subparsers.add_parser(
        "validate-fixtures",
        help="Validate local Stripe fixture JSON files.",
    )
    fixtures_parser.add_argument(
        "--path",
        default="apps/api-service/tests/fixtures/stripe",
        help=(
            "Directory containing *.json fixtures "
            "(default: apps/api-service/tests/fixtures/stripe)."
        ),
    )
    fixtures_parser.set_defaults(handler=handle_dispatch_validate_fixtures)


def handle_stripe_setup(args: argparse.Namespace, ctx: CLIContext) -> int:
    config = StripeSetupConfig(
        currency=args.currency,
        trial_days=args.trial_days,
        non_interactive=args.non_interactive,
        secret_key=args.secret_key,
        webhook_secret=args.webhook_secret,
        auto_webhook_secret=args.auto_webhook_secret,
        webhook_forward_url=args.webhook_forward_url,
        plan_overrides=args.plan or [],
        skip_postgres=args.skip_postgres_check,
        skip_stripe_cli=args.skip_stripe_cli,
    )
    run_stripe_setup(ctx, config)
    return 0


def handle_webhook_secret(args: argparse.Namespace, ctx: CLIContext) -> int:
    config = WebhookSecretConfig(
        forward_url=args.forward_url,
        print_only=args.print_only,
        skip_stripe_cli=args.skip_stripe_cli,
    )
    run_webhook_secret(ctx, config)
    return 0


def handle_dispatch_list(args: argparse.Namespace, ctx: CLIContext) -> int:
    config = DispatchListConfig(
        handler=args.handler,
        status=args.status,
        limit=args.limit,
        page=args.page,
    )
    return run_dispatch_list(ctx, config)


def handle_dispatch_replay(args: argparse.Namespace, ctx: CLIContext) -> int:
    config = DispatchReplayConfig(
        dispatch_ids=args.dispatch_id,
        event_ids=args.event_id,
        status=args.status,
        limit=args.limit,
        handler=args.handler,
        assume_yes=args.yes,
    )
    return run_dispatch_replay(ctx, config)


def handle_dispatch_validate_fixtures(args: argparse.Namespace, ctx: CLIContext) -> int:
    return run_dispatch_validate_fixtures(ctx, args.path)
