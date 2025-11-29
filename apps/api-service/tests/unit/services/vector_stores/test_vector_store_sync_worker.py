from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.infrastructure.persistence.vector_stores.models import VectorStore, VectorStoreFile
from app.services.vector_stores import VectorStoreSyncWorker
from tests.utils.sqlalchemy import create_tables


class _RemoteStore:
    def __init__(self):
        self.id = "vs_123"
        self.status = "ready"
        self.usage_bytes = 10
        self.expires_at = None
        self.last_active_at = datetime.now(UTC)


class _RemoteFile:
    def __init__(self, file_id: str = "file1", status: str = "completed", usage: int = 10):
        self.id = file_id
        self.status = status
        self.usage_bytes = usage
        self.last_error = None


class _FakeOpenAI:
    def __init__(self, remote_store: _RemoteStore, remote_files: list[_RemoteFile]):
        self._remote_store = remote_store
        self._remote_files = remote_files

    class _Files:
        def __init__(self, remote_files: list[_RemoteFile]):
            self._remote_files = remote_files

        async def list(self, *, vector_store_id: str, after: str | None = None, limit: int = 200):
            # Simple pagination: return one item per page to exercise has_more/last_id handling.
            ids = [f.id for f in self._remote_files]
            start = 0
            if after and after in ids:
                start = ids.index(after) + 1
            slice_items = self._remote_files[start : start + 1]
            has_more = start + 1 < len(self._remote_files)
            last_id = slice_items[-1].id if slice_items else None
            return type(
                "List",
                (),
                {"data": slice_items, "has_more": has_more, "last_id": last_id},
            )

    class _VectorStores:
        def __init__(self, outer):
            self._outer = outer
            self.files = _FakeOpenAI._Files(outer._remote_files)

        async def retrieve(self, vector_store_id: str):  # pragma: no cover - trivial
            return self._outer._remote_store

    @property
    def vector_stores(self):  # pragma: no cover - trivial
        return _FakeOpenAI._VectorStores(self)


@pytest.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(create_tables, (VectorStore.__table__, VectorStoreFile.__table__))
    try:
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_sync_worker_updates_status(session_factory):
    remote_store = _RemoteStore()
    remote_file = _RemoteFile()

    async with session_factory() as session:
        store = VectorStore(
            id=uuid4(),
            openai_id=remote_store.id,
            tenant_id=uuid4(),
            owner_user_id=None,
            name="primary",
            description=None,
            status="creating",
            usage_bytes=0,
            metadata_json={},
        )
        session.add(store)
        await session.commit()

    client = _FakeOpenAI(remote_store, [remote_file])
    worker = VectorStoreSyncWorker(
        session_factory=session_factory,
        settings_factory=lambda: None,
        client_factory=lambda _tenant: client,
        poll_interval_seconds=0.1,
        batch_size=10,
    )

    # call a single cycle
    await worker._sync_cycle()

    async with session_factory() as session:
        refreshed = await session.get(VectorStore, store.id)
        assert refreshed.status == "ready"
        assert refreshed.usage_bytes == remote_store.usage_bytes


@pytest.mark.asyncio
async def test_sync_worker_updates_usage_to_zero(session_factory):
    remote_store = _RemoteStore()
    remote_file = _RemoteFile()

    async with session_factory() as session:
        store = VectorStore(
            id=uuid4(),
            openai_id=remote_store.id,
            tenant_id=uuid4(),
            owner_user_id=None,
            name="primary",
            description=None,
            status="creating",
            usage_bytes=5,
            metadata_json={},
        )
        session.add(store)
        await session.commit()

    client = _FakeOpenAI(remote_store, [remote_file])
    worker = VectorStoreSyncWorker(
        session_factory=session_factory,
        settings_factory=lambda: None,
        client_factory=lambda _tenant: client,
        poll_interval_seconds=0.1,
        batch_size=10,
    )

    await worker._sync_cycle()
    # drop remote usage to zero and ensure it propagates
    remote_store.usage_bytes = 0
    await worker._sync_cycle()

    async with session_factory() as session:
        refreshed = await session.get(VectorStore, store.id)
        assert refreshed.usage_bytes == 0


@pytest.mark.asyncio
async def test_sync_worker_paginates_files(session_factory):
    remote_store = _RemoteStore()
    remote_files = [
        _RemoteFile("file1", status="completed", usage=10),
        _RemoteFile("file2", status="failed", usage=5),
    ]

    async with session_factory() as session:
        store = VectorStore(
            id=uuid4(),
            openai_id=remote_store.id,
            tenant_id=uuid4(),
            owner_user_id=None,
            name="primary",
            description=None,
            status="ready",
            usage_bytes=0,
            metadata_json={},
        )
        session.add(store)
        session.add_all(
            [
                VectorStoreFile(
                    id=uuid4(),
                    openai_file_id="file1",
                    vector_store_id=store.id,
                    filename="f1",
                    mime_type="text/plain",
                    size_bytes=1,
                    status="indexing",
                    usage_bytes=0,
                    attributes_json={},
                ),
                VectorStoreFile(
                    id=uuid4(),
                    openai_file_id="file2",
                    vector_store_id=store.id,
                    filename="f2",
                    mime_type="text/plain",
                    size_bytes=1,
                    status="indexing",
                    usage_bytes=0,
                    attributes_json={},
                ),
            ]
        )
        await session.commit()

    client = _FakeOpenAI(remote_store, remote_files)
    worker = VectorStoreSyncWorker(
        session_factory=session_factory,
        settings_factory=lambda: None,
        client_factory=lambda _tenant: client,
        poll_interval_seconds=0.1,
        batch_size=10,
    )

    await worker._sync_cycle()

    async with session_factory() as session:
        rows = await session.scalars(
            select(VectorStoreFile).where(VectorStoreFile.vector_store_id == store.id)
        )
        files = {row.openai_file_id: row for row in rows}
        assert files["file1"].status == "completed"
        assert files["file1"].usage_bytes == 10
        assert files["file2"].status == "failed"
        assert files["file2"].usage_bytes == 5
