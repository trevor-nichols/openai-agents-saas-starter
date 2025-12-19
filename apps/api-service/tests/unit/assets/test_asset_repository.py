import uuid

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.domain.assets import AssetRecord
from app.infrastructure.persistence.assets.repository import SqlAlchemyAssetRepository
from app.infrastructure.persistence.models.base import Base
from app.infrastructure.persistence.storage.models import StorageBucket, StorageObject


@pytest.mark.asyncio
async def test_asset_repository_create_list_and_link_message() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    tenant_id = uuid.uuid4()
    bucket_id = uuid.uuid4()
    object_id = uuid.uuid4()

    async with session_factory() as session:
        bucket = StorageBucket(
            id=bucket_id,
            tenant_id=tenant_id,
            provider="memory",
            bucket_name="test-bucket",
            region=None,
            prefix=None,
            is_default=True,
            status="ready",
        )
        obj = StorageObject(
            id=object_id,
            tenant_id=tenant_id,
            bucket_id=bucket_id,
            object_key=f"{tenant_id}/{object_id}/asset.png",
            filename="asset.png",
            mime_type="image/png",
            size_bytes=1024,
            checksum_sha256=None,
            status="ready",
            created_by_user_id=None,
            agent_key="image_studio",
            conversation_id=None,
            metadata_json={"source": "test"},
        )
        session.add(bucket)
        session.add(obj)
        await session.commit()

    repo = SqlAlchemyAssetRepository(session_factory)
    record = AssetRecord(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        storage_object_id=object_id,
        asset_type="image",
        source_tool="image_generation",
        conversation_id=None,
        message_id=None,
        tool_call_id="tool-1",
        response_id="resp-1",
        container_id=None,
        openai_file_id=None,
        metadata={"kind": "chart"},
    )

    created = await repo.create(record)
    assert created.storage_object_id == object_id

    items = await repo.list(
        tenant_id=tenant_id,
        limit=10,
        offset=0,
        asset_type="image",
    )
    assert len(items) == 1
    view = items[0]
    assert view.filename == "asset.png"
    assert view.mime_type == "image/png"
    assert view.asset.source_tool == "image_generation"

    linked = await repo.link_message(
        tenant_id=tenant_id,
        message_id=42,
        storage_object_ids=[object_id],
    )
    assert linked == 1
    updated = await repo.get_record(tenant_id=tenant_id, asset_id=created.id)
    assert updated is not None
    assert updated.message_id == 42

    duplicate = await repo.create(record)
    assert duplicate.id == created.id

    await engine.dispose()
