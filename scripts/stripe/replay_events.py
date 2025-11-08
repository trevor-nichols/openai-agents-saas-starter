#!/usr/bin/env python
"""CLI helper for inspecting and replaying stored Stripe events."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from pathlib import Path
from typing import Iterable

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
from app.infrastructure.persistence.billing import PostgresBillingRepository  # noqa: E402
from app.infrastructure.persistence.stripe.repository import (  # noqa: E402
    StripeEventRepository,
    StripeDispatchStatus,
)
from app.services.billing_service import billing_service  # noqa: E402
from app.services.stripe_dispatcher import stripe_event_dispatcher  # noqa: E402

FIXTURES_DIR = REPO_ROOT / "anything-agents" / "tests" / "fixtures" / "stripe"


def load_env_files() -> None:
    for candidate in (REPO_ROOT / ".env.local", REPO_ROOT / ".env"):
        if candidate.exists():
            load_dotenv(candidate)
            break


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stripe event tooling")
    sub = parser.add_subparsers(dest="command")

    list_cmd = sub.add_parser("list", help="List stored Stripe dispatches")
    list_cmd.add_argument("--status", choices=[s.value for s in StripeDispatchStatus] + ["all"], default="failed")
    list_cmd.add_argument("--handler", default="billing_sync")
    list_cmd.add_argument("--limit", type=int, default=20)
    list_cmd.add_argument("--page", type=int, default=1, help="Page number (1-indexed)")

    replay_cmd = sub.add_parser("replay", help="Replay stored dispatches through the dispatcher")
    replay_cmd.add_argument("--dispatch-id", action="append", help="Specific dispatch UUID(s) to replay")
    replay_cmd.add_argument("--event-id", action="append", help="Replay dispatches derived from Stripe event IDs")
    replay_cmd.add_argument("--status", choices=[s.value for s in StripeDispatchStatus], help="Replay by status")
    replay_cmd.add_argument("--limit", type=int, default=5, help="Limit when replaying by status")
    replay_cmd.add_argument("--handler", default="billing_sync")
    replay_cmd.add_argument("--yes", action="store_true", help="Skip confirmation prompt")

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
    billing_repository = PostgresBillingRepository(session_factory)
    billing_service.set_repository(billing_repository)
    return StripeEventRepository(session_factory)


async def shutdown_repository() -> None:
    await dispose_engine()
    config_module.get_settings.cache_clear()


async def cmd_list(
    repo: StripeEventRepository,
    handler: str,
    status: str,
    limit: int,
    *,
    page: int,
) -> None:
    status_filter = None if status == "all" else status
    offset = max(page - 1, 0) * limit
    dispatches = await repo.list_dispatches(handler=handler, status=status_filter, limit=limit, offset=offset)
    if not dispatches:
        print("No dispatches found.")
        return
    print(f"Page {page} (limit {limit})")
    for dispatch, event in dispatches:
        print(
            f"{dispatch.id}\t{dispatch.status}\thandler={dispatch.handler}\tattempts={dispatch.attempts}\t"
            f"event={event.stripe_event_id} ({event.event_type})\ttenant={event.tenant_hint}"
        )


async def cmd_replay(
    repo: StripeEventRepository,
    *,
    dispatch_ids: Iterable[str] | None,
    event_ids: Iterable[str] | None,
    status: str | None,
    limit: int,
    handler: str,
    assume_yes: bool,
) -> None:
    dispatcher = stripe_event_dispatcher
    stripe_event_dispatcher.configure(repository=repo, billing=billing_service)

    targets: list[uuid.UUID] = []
    if dispatch_ids:
        for dispatch_id in dispatch_ids:
            targets.append(uuid.UUID(dispatch_id))
    elif event_ids:
        for event_id in event_ids:
            event = await repo.get_by_event_id(event_id)
            if event is None:
                print(f"⚠️  Event {event_id} not found; skipping")
                continue
            dispatch = await repo.ensure_dispatch(event_id=event.id, handler=handler)
            targets.append(dispatch.id)
    elif status:
        rows = await repo.list_dispatches(handler=handler, status=status, limit=limit)
        targets.extend(row[0].id for row in rows)
    else:
        raise SystemExit("Provide --dispatch-id, --event-id, or --status for replay.")

    if not targets:
        print("No dispatches to replay.")
        return

    if not _confirm_replay(targets, assume_yes=assume_yes):
        print("Aborted by user.")
        return

    for dispatch_id in targets:
        try:
            result = await dispatcher.replay_dispatch(dispatch_id)
            when = result.processed_at.isoformat() if result.processed_at else "n/a"
            print(f"✅ Replayed dispatch {dispatch_id} (processed_at={when})")
        except Exception as exc:  # pragma: no cover - CLI surface
            print(f"❌ Failed to replay {dispatch_id}: {exc}")


def _confirm_replay(targets: list[uuid.UUID], *, assume_yes: bool) -> bool:
    if assume_yes or not targets:
        return True
    preview = "\n".join(str(t) for t in targets[:5])
    if len(targets) > 5:
        preview += f"\n...and {len(targets) - 5} more"
    print("About to replay the following dispatch IDs:")
    print(preview)
    answer = input("Proceed? [y/N]: ").strip().lower()
    return answer in {"y", "yes"}


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
            await cmd_list(
                repo,
                handler=args.handler,
                status=args.status,
                limit=args.limit,
                page=args.page,
            )
        elif args.command == "replay":
            await cmd_replay(
                repo,
                dispatch_ids=args.dispatch_id,
                event_ids=args.event_id,
                status=args.status,
                limit=args.limit,
                handler=args.handler,
                assume_yes=args.yes,
            )
        else:
            raise SystemExit("Unknown command")
    finally:
        await shutdown_repository()


if __name__ == "__main__":
    asyncio.run(main())
