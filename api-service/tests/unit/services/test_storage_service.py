from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pytest

from app.domain.storage import StorageProviderLiteral
from app.infrastructure.storage.providers.memory import MemoryStorageProvider
from app.services.storage.service import StorageService


@dataclass
class _FakeSettings:
    storage_provider: StorageProviderLiteral = StorageProviderLiteral.MEMORY
    storage_bucket_prefix: str = "agent-data"
    storage_signed_url_ttl_seconds: int = 900
    storage_max_file_mb: int = 1
    storage_allowed_mime_types: list[str] = field(
        default_factory=lambda: ["text/plain", "application/json"]
    )
    minio_region: str | None = None


@dataclass
class _FakeBucket:
    id: uuid.UUID
    tenant_id: uuid.UUID
    provider: str
    bucket_name: str
    region: str | None = None
    prefix: str | None = None


@dataclass
class _FakeObject:
    id: uuid.UUID
    tenant_id: uuid.UUID
    bucket_id: uuid.UUID
    bucket: _FakeBucket
    object_key: str
    filename: str
    mime_type: str | None
    size_bytes: int | None
    checksum_sha256: str | None
    status: str
    created_by_user_id: uuid.UUID | None
    agent_key: str | None
    conversation_id: uuid.UUID | None
    metadata_json: dict[str, object]
    expires_at: datetime | None
    deleted_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class _FakeRepo:
    def __init__(self) -> None:
        self.buckets: dict[tuple[uuid.UUID, str], _FakeBucket] = {}
        self.objects: dict[uuid.UUID, _FakeObject] = {}

    async def get_or_create_bucket(
        self,
        *,
        tenant_id: uuid.UUID,
        provider: str,
        bucket_name: str,
        region: str | None,
        prefix: str | None,
    ) -> _FakeBucket:
        key = (tenant_id, bucket_name)
        if key not in self.buckets:
            self.buckets[key] = _FakeBucket(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                provider=provider,
                bucket_name=bucket_name,
                region=region,
                prefix=prefix,
            )
        return self.buckets[key]

    async def create_object(
        self,
        *,
        tenant_id: uuid.UUID,
        bucket: _FakeBucket,
        object_id: uuid.UUID,
        object_key: str,
        filename: str,
        mime_type: str | None,
        size_bytes: int | None,
        checksum_sha256: str | None,
        status: str,
        created_by_user_id: uuid.UUID | None,
        agent_key: str | None,
        conversation_id: uuid.UUID | None,
        metadata_json: dict[str, object],
        expires_at: datetime | None,
    ) -> _FakeObject:
        obj = _FakeObject(
            id=object_id,
            tenant_id=tenant_id,
            bucket_id=bucket.id,
            bucket=bucket,
            object_key=object_key,
            filename=filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            checksum_sha256=checksum_sha256,
            status=status,
            created_by_user_id=created_by_user_id,
            agent_key=agent_key,
            conversation_id=conversation_id,
            metadata_json=metadata_json,
            expires_at=expires_at,
        )
        self.objects[obj.id] = obj
        return obj

    async def get_object_for_tenant(self, *, tenant_id: uuid.UUID, object_id: uuid.UUID):
        obj = self.objects.get(object_id)
        if obj and obj.tenant_id == tenant_id:
            return obj
        return None

    async def list_objects(
        self, *, tenant_id: uuid.UUID, limit: int, offset: int, conversation_id=None
    ):
        objs = [o for o in self.objects.values() if o.tenant_id == tenant_id]
        return objs[offset : offset + limit]

    async def mark_deleted(self, *, object_id: uuid.UUID) -> None:
        if object_id in self.objects:
            self.objects[object_id].deleted_at = datetime.utcnow()


def _service(repo: _FakeRepo, settings: _FakeSettings | None = None) -> StorageService:
    settings = settings or _FakeSettings()
    settings_any: Any = settings
    provider = MemoryStorageProvider()
    return StorageService(
        session_factory=None,
        settings_provider=lambda: settings_any,
        provider_resolver=lambda _settings: provider,
        repository=repo,  # type: ignore[arg-type]
    )


@pytest.mark.asyncio
async def test_presign_upload_sanitizes_filename_and_persists_metadata():
    repo = _FakeRepo()
    service = _service(repo)
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()

    resp = await service.create_presigned_upload(
        tenant_id=tenant_id,
        user_id=user_id,
        filename="My File (draft).txt",
        mime_type="text/plain",
        size_bytes=10,
        metadata={"k": "v"},
    )

    assert resp.object_id in repo.objects
    obj = repo.objects[resp.object_id]
    assert obj.filename == "My File (draft).txt"
    # object key should include tenant and sanitized filename
    assert obj.object_key.endswith("My-File-draft-.txt")
    assert repo.buckets[(tenant_id, obj.bucket.bucket_name)].tenant_id == tenant_id


@pytest.mark.asyncio
async def test_presign_upload_rejects_oversize():
    repo = _FakeRepo()
    settings = _FakeSettings(storage_max_file_mb=1)
    service = _service(repo, settings=settings)
    tenant_id = uuid.uuid4()

    with pytest.raises(ValueError):
        await service.create_presigned_upload(
            tenant_id=tenant_id,
            user_id=None,
            filename="big.bin",
            mime_type="application/octet-stream",
            size_bytes=2 * 1024 * 1024,  # 2 MB > 1 MB limit
        )
