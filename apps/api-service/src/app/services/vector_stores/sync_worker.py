"""Background worker to refresh vector store/file status and apply expiry."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from agents import trace
from openai import AsyncOpenAI
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql.elements import ColumnElement

from app.core.settings import Settings
from app.infrastructure.persistence.vector_stores.models import VectorStore, VectorStoreFile

logger = logging.getLogger(__name__)


class OpenAIClientFactory(Protocol):
    def __call__(self, tenant_id: UUID) -> AsyncOpenAI: ...


class VectorStoreSyncWorker:
    """Periodically refreshes remote vector store + file state and handles expiry."""

    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        settings_factory,
        client_factory: OpenAIClientFactory,
        poll_interval_seconds: float = 60.0,
        batch_size: int = 20,
        auto_purge_expired: bool = False,
    ) -> None:
        self._session_factory = session_factory
        self._settings_factory = settings_factory
        self._client_factory = client_factory
        self._poll_interval_seconds = max(5.0, poll_interval_seconds)
        self._batch_size = max(1, batch_size)
        self._auto_purge_expired = auto_purge_expired
        self._task: asyncio.Task[None] | None = None
        self._stop_event: asyncio.Event | None = None

    async def start(self) -> None:
        if self._task is not None:
            return
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self._run(), name="vector-store-sync")

    async def shutdown(self) -> None:
        if self._task is None:
            return
        stop_event = self._require_stop_event()
        stop_event.set()
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:  # pragma: no cover - normal path
            pass
        finally:
            self._task = None
            self._stop_event = None

    async def _run(self) -> None:
        stop_event = self._require_stop_event()
        while not stop_event.is_set():
            try:
                await self._sync_cycle()
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("vector_store.sync_cycle_failed", exc_info=exc)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=self._poll_interval_seconds)
            except TimeoutError:
                continue

    async def _sync_cycle(self) -> None:
        now = datetime.now(UTC)
        stop_event = self._stop_event or asyncio.Event()
        last_created_at: datetime | None = None
        last_id: UUID | None = None

        while not stop_event.is_set():
            conditions: list[ColumnElement[bool]] = [
                VectorStore.deleted_at.is_(None),
                VectorStore.status.in_(["creating", "indexing", "in_progress", "ready"]),
            ]
            if last_created_at is not None and last_id is not None:
                conditions.append(
                    or_(
                        VectorStore.created_at > last_created_at,
                        and_(
                            VectorStore.created_at == last_created_at,
                            VectorStore.id > last_id,
                        ),
                    )
                )

            async with self._session_factory() as session:
                stores = await session.scalars(
                    select(VectorStore)
                    .where(*conditions)
                    .order_by(VectorStore.created_at.asc(), VectorStore.id.asc())
                    .limit(self._batch_size)
                )
                batch = list(stores)

            if not batch:
                break

            for store in batch:
                await self._refresh_store(store, now)
                if stop_event.is_set():
                    break

            last_created_at = batch[-1].created_at
            last_id = batch[-1].id

    async def _refresh_store(self, store: VectorStore, now: datetime) -> None:
        client = self._client_factory(store.tenant_id)
        try:
            with trace(
                workflow_name="vector_store.sync_store",
                metadata={"tenant_id": str(store.tenant_id), "vector_store_id": str(store.id)},
            ):
                remote_store = await client.vector_stores.retrieve(store.openai_id)
        except Exception as exc:  # pragma: no cover - network issues
            logger.warning(
                "vector_store.sync_remote_failed",
                extra={"tenant_id": str(store.tenant_id), "vector_store_id": str(store.id)},
                exc_info=exc,
            )
            return

        status = getattr(remote_store, "status", store.status)

        remote_usage = getattr(remote_store, "usage_bytes", None)
        usage_bytes = store.usage_bytes if remote_usage is None else remote_usage

        expires_at = getattr(remote_store, "expires_at", None) or store.expires_at
        last_active_at = getattr(remote_store, "last_active_at", None) or store.last_active_at

        # Expiry enforcement
        expired = expires_at is not None and expires_at <= now

        async with self._session_factory() as session:
            db_store = await session.get(VectorStore, store.id)
            if db_store is None or db_store.deleted_at is not None:
                return
            db_store.status = "expired" if expired else status
            db_store.usage_bytes = usage_bytes
            db_store.expires_at = expires_at
            db_store.last_active_at = last_active_at
            await session.commit()

        if expired and self._auto_purge_expired:
            await self._purge_store(client, store)
            return

        await self._refresh_files(store, client)

    async def _refresh_files(self, store: VectorStore, client: AsyncOpenAI) -> None:
        try:
            with trace(
                workflow_name="vector_store.sync_files",
                metadata={"tenant_id": str(store.tenant_id), "vector_store_id": str(store.id)},
            ):
                remote_index: dict[str, object] = {}
                after: str | None = None
                while True:
                    if after is None:
                        page = await client.vector_stores.files.list(
                            vector_store_id=store.openai_id,
                            limit=200,
                        )
                    else:
                        page = await client.vector_stores.files.list(
                            vector_store_id=store.openai_id,
                            limit=200,
                            after=after,
                        )
                    for item in getattr(page, "data", []):
                        remote_index[item.id] = item
                    has_more = getattr(page, "has_more", False)
                    last_id = getattr(page, "last_id", None)
                    if has_more and last_id:
                        after = last_id
                        continue
                    break
        except Exception as exc:  # pragma: no cover - network issues
            logger.warning(
                "vector_store.sync_files_failed",
                extra={"tenant_id": str(store.tenant_id), "vector_store_id": str(store.id)},
                exc_info=exc,
            )
            return
        async with self._session_factory() as session:
            rows = await session.scalars(
                select(VectorStoreFile).where(
                    VectorStoreFile.vector_store_id == store.id,
                    VectorStoreFile.deleted_at.is_(None),
                    VectorStoreFile.status.in_(["indexing", "in_progress", "failed", "completed"]),
                )
            )
            for row in rows:
                remote = remote_index.get(row.openai_file_id)
                if remote is None:
                    continue
                row.status = getattr(remote, "status", row.status)
                remote_usage = getattr(remote, "usage_bytes", None)
                row.usage_bytes = row.usage_bytes if remote_usage is None else remote_usage
                row.last_error = getattr(remote, "last_error", row.last_error)
            await session.commit()

    async def _purge_store(self, client: AsyncOpenAI, store: VectorStore) -> None:
        try:
            with trace(
                workflow_name="vector_store.purge_store",
                metadata={"tenant_id": str(store.tenant_id), "vector_store_id": str(store.id)},
            ):
                await client.vector_stores.delete(store.openai_id)
        except Exception as exc:  # pragma: no cover - network issues
            logger.warning(
                "vector_store.purge_failed",
                extra={"tenant_id": str(store.tenant_id), "vector_store_id": str(store.id)},
                exc_info=exc,
            )
            return

        async with self._session_factory() as session:
            db_store = await session.get(VectorStore, store.id)
            if db_store:
                db_store.deleted_at = datetime.now(UTC)
                db_store.status = "deleted"
                await session.commit()

    def _require_stop_event(self) -> asyncio.Event:
        if self._stop_event is None:
            raise RuntimeError("VectorStoreSyncWorker not started")
        return self._stop_event


def build_vector_store_sync_worker(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    settings_factory,
    client_factory: OpenAIClientFactory,
) -> VectorStoreSyncWorker:
    settings: Settings = settings_factory()
    return VectorStoreSyncWorker(
        session_factory=session_factory,
        settings_factory=settings_factory,
        client_factory=client_factory,
        poll_interval_seconds=settings.vector_store_sync_poll_seconds,
        batch_size=settings.vector_store_sync_batch_size,
        auto_purge_expired=settings.auto_purge_expired_vector_stores,
    )


__all__ = ["VectorStoreSyncWorker", "build_vector_store_sync_worker"]
