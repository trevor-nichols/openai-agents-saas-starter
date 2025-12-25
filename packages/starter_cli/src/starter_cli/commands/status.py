from __future__ import annotations

import argparse

from starter_cli.core import CLIContext
from starter_cli.services.auth.status_ops import StatusOpsClient


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    status_parser = subparsers.add_parser("status", help="Status subscription operations.")
    status_subparsers = status_parser.add_subparsers(dest="status_command")

    subs_parser = status_subparsers.add_parser("subscriptions", help="Manage alert subscriptions.")
    subs_sub = subs_parser.add_subparsers(dest="subscriptions_command")

    list_parser = subs_sub.add_parser(
        "list",
        help="List active subscriptions (requires status:manage token).",
    )
    list_parser.add_argument("--limit", type=int, default=50, help="Results per page (default 50).")
    list_parser.add_argument("--cursor", help="Cursor for pagination.")
    list_parser.add_argument(
        "--tenant",
        dest="tenant_id",
        help="Tenant UUID to inspect (operators only).",
    )
    list_parser.set_defaults(handler=handle_subscriptions_list)

    revoke_parser = subs_sub.add_parser("revoke", help="Revoke a subscription by ID.")
    revoke_parser.add_argument("subscription_id", help="Subscription UUID.")
    revoke_parser.set_defaults(handler=handle_subscriptions_revoke)

    incidents_parser = status_subparsers.add_parser("incidents", help="Incident alert utilities.")
    incidents_sub = incidents_parser.add_subparsers(dest="incidents_command")

    resend_parser = incidents_sub.add_parser(
        "resend",
        help="Re-dispatch an incident to subscribers.",
    )
    resend_parser.add_argument("incident_id", help="Incident identifier from /status snapshot.")
    resend_parser.add_argument(
        "--severity",
        default="major",
        choices=["all", "major", "maintenance"],
        help="Severity used for filtering (default: major).",
    )
    resend_parser.add_argument(
        "--tenant",
        dest="tenant_id",
        help="Optional tenant UUID to scope notifications.",
    )
    resend_parser.set_defaults(handler=handle_incident_resend)


def handle_subscriptions_list(args: argparse.Namespace, ctx: CLIContext) -> int:
    console = ctx.console
    client = StatusOpsClient.from_env()
    result = client.list_subscriptions(
        limit=args.limit,
        cursor=args.cursor,
        tenant_id=args.tenant_id,
    )
    items = result.items
    if not items:
        console.info("No subscriptions found.", topic="status")
        return 0
    for item in items:
        console.info(
            f"[{item.status}] {item.target_masked} (channel={item.channel}, "
            f"severity={item.severity_filter}, id={item.id})",
            topic="status",
        )
    if result.next_cursor:
        console.info(f"Next cursor: {result.next_cursor}", topic="status")
    return 0


def handle_subscriptions_revoke(args: argparse.Namespace, ctx: CLIContext) -> int:
    console = ctx.console
    client = StatusOpsClient.from_env()
    client.revoke_subscription(args.subscription_id)
    console.success(f"Subscription {args.subscription_id} revoked.", topic="status")
    return 0


def handle_incident_resend(args: argparse.Namespace, ctx: CLIContext) -> int:
    console = ctx.console
    client = StatusOpsClient.from_env()
    result = client.resend_incident(
        incident_id=args.incident_id,
        severity=args.severity,
        tenant_id=args.tenant_id,
    )
    console.success(
        f"Incident {args.incident_id} dispatched to {result.dispatched} subscription(s).",
        topic="status",
    )
    return 0


__all__ = ["register"]
