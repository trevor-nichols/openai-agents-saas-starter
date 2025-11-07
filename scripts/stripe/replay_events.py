#!/usr/bin/env python
"""CLI helper for inspecting and replaying stored Stripe events."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import hmac
import json
import sys
import time
from pathlib import Path
from typing import Iterable

import httpx
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
ANYTHING_AGENTS_DIR = REPO_ROOT / "anything-agents"
if str(ANYTHING_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(ANYTHING_AGENTS_DIR))

from app.core import config as config_module  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.infrastructure.db import (  # noqa: E402
    dispose_engine,
    get_async_sessionmaker,
    init_engine,
)
from app.infrastructure.persistence.stripe.repository import (  # noqa: E402
    StripeEventRepository,
    StripeEventStatus,
)

FIXTURES_DIR = REPO_ROOT / "anything-agents" / "tests" / "fixtures" / "stripe"


def load_env_files() -> None:
    for candidate in (REPO_ROOT / ".env.local", REPO_ROOT / ".env"):
        if candidate.exists():
            load_dotenv(candidate)
            break


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stripe event tooling")
    sub = parser.add_subparsers(dest="command")

    list_cmd = sub.add_parser("list", help="List stored Stripe events")
    list_cmd.add_argument("--status", choices=[s.value for s in StripeEventStatus] + ["all"], default="failed")
    list_cmd.add_argument("--limit", type=int, default=20)

    replay_cmd = sub.add_parser("replay", help="Replay stored events back into the webhook")
    replay_cmd.add_argument("--event-id", action="append", help="Specific Stripe event ID(s) to replay")
    replay_cmd.add_argument("--status", choices=[s.value for s in StripeEventStatus], help="Replay by status")
    replay_cmd.add_argument("--limit", type=int, default=5, help="Limit when replaying by status")
    replay_cmd.add_argument(
        "--webhook-url",
        default="http://localhost:8000/webhooks/stripe",
        help="Webhook endpoint to call",
    )
    replay_cmd.add_argument("--dry-run", action="store_true", help="Print payloads without POSTing")

    fixtures_cmd = sub.add_parser("validate-fixtures", help="Validate local Stripe fixture JSON files")
    fixtures_cmd.add_argument(
        "--path",
        default=str(FIXTURES_DIR),
        help="Directory containing *.json fixtures",
    )

    parser.set_defaults(command="list")
    return parser.parse_args()


async def init_repository() -> StripeEventRepository:
    config_module.get_settings.cache_clear()
    await init_engine(run_migrations=False)
    session_factory = get_async_sessionmaker()
    return StripeEventRepository(session_factory)


async def shutdown_repository() -> None:
    await dispose_engine()
    config_module.get_settings.cache_clear()


async def cmd_list(repo: StripeEventRepository, status: str, limit: int) -> None:
    status_filter = None if status == "all" else status
    events = await repo.list_events(status=status_filter, limit=limit)
    if not events:
        print("No events found.")
        return
    for event in events:
        print(
            f"{event.stripe_event_id}\t{event.event_type}\ttenant={event.tenant_hint}\tstatus={event.processing_outcome}\t"
            f"received={event.received_at.isoformat() if event.received_at else 'unknown'}"
        )


async def cmd_replay(
    repo: StripeEventRepository,
    *,
    event_ids: Iterable[str] | None,
    status: str | None,
    limit: int,
    webhook_url: str,
    dry_run: bool,
) -> None:
    settings = get_settings()
    secret = settings.stripe_webhook_secret
    if not secret:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET must be configured to compute webhook signatures.")

    events = []
    if event_ids:
        for event_id in event_ids:
            record = await repo.get_by_event_id(event_id)
            if record is None:
                print(f"⚠️  Event {event_id} not found; skipping")
                continue
            events.append(record)
    elif status:
        events = await repo.list_events(status=status, limit=limit)
    else:
        raise SystemExit("Either --event-id or --status is required for replay.")

    if not events:
        print("No events to replay.")
        return

    async with httpx.AsyncClient(timeout=30.0) as client:
        for event in events:
            payload = json.dumps(event.payload, separators=(",", ":"), sort_keys=True)
            if dry_run:
                print(f"🛈 Dry-run: would replay {event.stripe_event_id} ({event.event_type})")
                continue
            timestamp = int(time.time())
            signed_payload = f"{timestamp}.{payload}".encode("utf-8")
            signature = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
            headers = {
                "stripe-signature": f"t={timestamp},v1={signature}",
                "content-type": "application/json",
            }
            response = await client.post(webhook_url, content=payload, headers=headers)
            status_code = response.status_code
            if status_code >= 400:
                print(f"❌ Failed to replay {event.stripe_event_id}: HTTP {status_code} -> {response.text}")
            else:
                print(f"✅ Replayed {event.stripe_event_id} ({event.event_type}) -> HTTP {status_code}")


def validate_fixtures(path: str) -> None:
    directory = Path(path)
    if not directory.exists():
        raise SystemExit(f"Fixture directory '{directory}' not found.")
    failures = 0
    for file in sorted(directory.glob("*.json")):
        try:
            json.loads(file.read_text(encoding="utf-8"))
            print(f"✅ {file.relative_to(directory)}")
        except json.JSONDecodeError as exc:
            failures += 1
            print(f"❌ {file} invalid JSON: {exc}")
    if failures:
        raise SystemExit(f"Fixture validation failed ({failures} files).")


async def main() -> None:
    load_env_files()
    args = parse_args()
    if args.command == "validate-fixtures":
        validate_fixtures(args.path)
        return

    repo = await init_repository()
    try:
        if args.command == "list":
            await cmd_list(repo, status=args.status, limit=args.limit)
        elif args.command == "replay":
            if not args.event_id and not args.status:
                raise SystemExit("--event-id or --status is required for replay.")
            await cmd_replay(
                repo,
                event_ids=args.event_id,
                status=args.status,
                limit=args.limit,
                webhook_url=args.webhook_url,
                dry_run=args.dry_run,
            )
        else:
            raise SystemExit("Unknown command")
    finally:
        await shutdown_repository()


if __name__ == "__main__":
    asyncio.run(main())
