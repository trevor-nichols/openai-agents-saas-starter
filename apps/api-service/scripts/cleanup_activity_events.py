"""Delete aged activity_events rows based on configured TTL.

Intended to be run via `just cleanup-activity-events` so env files are loaded.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.infrastructure.db import get_async_sessionmaker
from app.infrastructure.persistence.activity.models import ActivityEventRow

logger = logging.getLogger(__name__)


async def _delete_batch(session: AsyncSession, cutoff: datetime, batch_size: int) -> int:
    ids: Sequence[str] = (
        await session.execute(
            select(ActivityEventRow.id)
            .where(ActivityEventRow.created_at < cutoff)
            .order_by(ActivityEventRow.id)
            .limit(batch_size)
        )
    ).scalars().all()

    if not ids:
        return 0

    await session.execute(delete(ActivityEventRow).where(ActivityEventRow.id.in_(ids)))
    await session.commit()
    return len(ids)


async def run_cleanup(ttl_days: int, batch_size: int, sleep_ms: int, dry_run: bool) -> None:
    cutoff = datetime.now(UTC) - timedelta(days=ttl_days)
    session_factory = get_async_sessionmaker()

    logger.info(
        "cleanup_activity_events.start",
        extra={"ttl_days": ttl_days, "batch_size": batch_size, "sleep_ms": sleep_ms},
    )

    async with session_factory() as session:
        total_deleted = 0
        while True:
            if dry_run:
                count = len(
                    (
                        await session.execute(
                            select(ActivityEventRow.id).where(ActivityEventRow.created_at < cutoff)
                        )
                    ).scalars().all()
                )
                logger.info(
                    "cleanup_activity_events.dry_run",
                    extra={"matches": count, "cutoff": cutoff.isoformat()},
                )
                break

            deleted = await _delete_batch(session, cutoff, batch_size)
            if deleted == 0:
                break
            total_deleted += deleted
            logger.info(
                "cleanup_activity_events.batch_deleted",
                extra={"deleted": deleted, "total_deleted": total_deleted},
            )
            if sleep_ms:
                await asyncio.sleep(sleep_ms / 1000)

    logger.info("cleanup_activity_events.complete", extra={"total_deleted": total_deleted})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cleanup aged activity_events rows")
    parser.add_argument("--days", type=int, default=None, help="TTL in days (override settings)")
    parser.add_argument("--batch", type=int, default=None, help="Delete batch size override")
    parser.add_argument(
        "--sleep-ms",
        type=int,
        default=None,
        help="Sleep milliseconds between batches",
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not delete, just count")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()

    ttl_days = args.days if args.days is not None else settings.activity_events_ttl_days
    batch_size = (
        args.batch if args.batch is not None else settings.activity_events_cleanup_batch_size
    )
    sleep_ms = (
        args.sleep_ms
        if args.sleep_ms is not None
        else settings.activity_events_cleanup_sleep_ms
    )

    asyncio.run(run_cleanup(ttl_days, batch_size, sleep_ms, args.dry_run))


if __name__ == "__main__":  # pragma: no cover - manual utility
    logging.basicConfig(level=logging.INFO)
    main()

