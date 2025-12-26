from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid
from dataclasses import dataclass
from typing import Any

from app.core.settings import get_settings
from app.infrastructure.db import dispose_engine, get_async_sessionmaker, init_engine
from app.infrastructure.persistence.billing import PostgresBillingRepository
from app.infrastructure.persistence.stripe.repository import StripeEventRepository
from app.services.billing.billing_service import billing_service
from app.services.billing.stripe.dispatcher import stripe_event_dispatcher


@dataclass(slots=True)
class ListArgs:
    status: str
    handler: str
    limit: int
    page: int


@dataclass(slots=True)
class ReplayArgs:
    dispatch_ids: list[str]
    event_ids: list[str]
    status: str | None
    limit: int
    handler: str
    preview: bool


async def _init_repo() -> StripeEventRepository:
    get_settings.cache_clear()
    await init_engine(run_migrations=False)
    session_factory = get_async_sessionmaker()
    billing_service.set_repository(PostgresBillingRepository(session_factory))
    return StripeEventRepository(session_factory)


async def _list_dispatches(args: ListArgs) -> dict[str, Any]:
    repo = await _init_repo()
    status_filter = None if args.status == "all" else args.status
    offset = max(args.page - 1, 0) * args.limit
    rows = await repo.list_dispatches(
        handler=args.handler,
        status=status_filter,
        limit=args.limit,
        offset=offset,
    )
    dispatches = [
        {
            "id": str(dispatch.id),
            "status": dispatch.status,
            "handler": dispatch.handler,
            "attempts": dispatch.attempts,
            "stripe_event_id": event.stripe_event_id,
            "event_type": event.event_type,
            "tenant_hint": event.tenant_hint,
        }
        for dispatch, event in rows
    ]
    return {
        "dispatches": dispatches,
        "page": args.page,
        "limit": args.limit,
        "status": args.status,
        "handler": args.handler,
    }


async def _replay_dispatches(args: ReplayArgs) -> dict[str, Any]:
    repo = await _init_repo()
    dispatcher = stripe_event_dispatcher
    dispatcher.configure(repository=repo, billing=billing_service)

    targets: list[uuid.UUID] = []
    if args.dispatch_ids:
        targets.extend(uuid.UUID(value) for value in args.dispatch_ids)
    elif args.event_ids:
        for event_id in args.event_ids:
            event = await repo.get_by_event_id(event_id)
            if event is None:
                continue
            dispatch = await repo.ensure_dispatch(event_id=event.id, handler=args.handler)
            targets.append(dispatch.id)
    elif args.status:
        rows = await repo.list_dispatches(handler=args.handler, status=args.status, limit=args.limit)
        targets.extend(row[0].id for row in rows)

    payload: dict[str, Any] = {"targets": [str(target) for target in targets]}
    if args.preview:
        return payload

    replayed: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for dispatch_id in targets:
        try:
            result = await dispatcher.replay_dispatch(dispatch_id)
            replayed.append(
                {
                    "id": str(dispatch_id),
                    "processed_at": result.processed_at.isoformat() if result.processed_at else "n/a",
                }
            )
        except Exception as exc:  # pragma: no cover - runtime
            errors.append({"id": str(dispatch_id), "error": str(exc)})
    payload.update({"replayed": replayed, "errors": errors})
    return payload


async def _run(args: argparse.Namespace) -> dict[str, Any]:
    try:
        if args.command == "list":
            list_args = ListArgs(
                status=args.status,
                handler=args.handler,
                limit=args.limit,
                page=args.page,
            )
            return await _list_dispatches(list_args)
        if args.command == "replay":
            replay_args = ReplayArgs(
                dispatch_ids=args.dispatch_id or [],
                event_ids=args.event_id or [],
                status=args.status,
                limit=args.limit,
                handler=args.handler,
                preview=bool(args.preview),
            )
            return await _replay_dispatches(replay_args)
        raise RuntimeError("Unknown command.")
    finally:
        await dispose_engine()
        get_settings.cache_clear()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stripe dispatch inspection helpers.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--status", default="failed")
    list_parser.add_argument("--handler", default="billing_sync")
    list_parser.add_argument("--limit", type=int, default=20)
    list_parser.add_argument("--page", type=int, default=1)

    replay_parser = subparsers.add_parser("replay")
    replay_parser.add_argument("--dispatch-id", action="append")
    replay_parser.add_argument("--event-id", action="append")
    replay_parser.add_argument("--status")
    replay_parser.add_argument("--limit", type=int, default=5)
    replay_parser.add_argument("--handler", default="billing_sync")
    replay_parser.add_argument("--preview", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Prevent SQL echo from polluting JSON output.
    os.environ["DATABASE_ECHO"] = "false"

    payload = asyncio.run(_run(args))
    print(json.dumps(payload, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
