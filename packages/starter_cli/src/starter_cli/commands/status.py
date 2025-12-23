from __future__ import annotations

import argparse
import os
from typing import Any

import httpx

from starter_cli.core import CLIContext, CLIError


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
    params: dict[str, Any] = {"limit": args.limit}
    if args.cursor is not None:
        params["cursor"] = args.cursor
    if args.tenant_id:
        params["tenant_id"] = args.tenant_id
    response = _request(
        method="GET",
        path="/api/v1/status/subscriptions",
        params=params,
    )
    data = response.json()
    items: list[dict[str, Any]] = data.get("items", [])
    if not items:
        console.info("No subscriptions found.", topic="status")
        return 0
    for item in items:
        console.info(
            "[{status}] {target} (channel={channel}, severity={severity}, id={sid})".format(
                status=item.get("status"),
                target=item.get("target_masked"),
                channel=item.get("channel"),
                severity=item.get("severity_filter"),
                sid=item.get("id"),
            ),
            topic="status",
        )
    if data.get("next_cursor"):
        console.info(f"Next cursor: {data['next_cursor']}", topic="status")
    return 0


def handle_subscriptions_revoke(args: argparse.Namespace, ctx: CLIContext) -> int:
    console = ctx.console
    _request(
        method="DELETE",
        path=f"/api/v1/status/subscriptions/{args.subscription_id}",
    )
    console.success(f"Subscription {args.subscription_id} revoked.", topic="status")
    return 0


def handle_incident_resend(args: argparse.Namespace, ctx: CLIContext) -> int:
    console = ctx.console
    payload: dict[str, Any] = {"severity": args.severity}
    if args.tenant_id:
        payload["tenant_id"] = args.tenant_id
    response = _request(
        method="POST",
        path=f"/api/v1/status/incidents/{args.incident_id}/resend",
        json_body=payload,
    )
    body = response.json()
    dispatched = body.get("dispatched", 0)
    console.success(
        f"Incident {args.incident_id} dispatched to {dispatched} subscription(s).",
        topic="status",
    )
    return 0


def _request(
    *,
    method: str,
    path: str,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> httpx.Response:
    token = os.getenv("STATUS_API_TOKEN")
    if not token:
        raise CLIError("STATUS_API_TOKEN is required to call status APIs.")
    base_url = os.getenv(
        "STATUS_API_BASE_URL",
        os.getenv("AUTH_CLI_BASE_URL", "http://127.0.0.1:8000"),
    )
    url = f"{base_url.rstrip('/')}{path}"
    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client(timeout=10.0) as client:
        response = client.request(method, url, params=params, json=json_body, headers=headers)
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail")
        except Exception:
            detail = response.text
        raise CLIError(f"Status API call failed ({response.status_code}): {detail}")
    return response


__all__ = ["register"]
