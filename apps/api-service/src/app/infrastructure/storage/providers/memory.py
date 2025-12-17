"""In-memory storage provider for tests/local development."""

from __future__ import annotations

import hashlib
from collections.abc import MutableMapping
from typing import Final

from app.domain.storage import (
    StorageObjectRef,
    StoragePresignedUrl,
    StorageProviderHealth,
    StorageProviderProtocol,
    StorageProviderStatus,
)


class MemoryStorageProvider(StorageProviderProtocol):
    """Non-persistent provider used for tests and local runs."""

    _scheme: Final[str] = "memory"

    def __init__(self) -> None:
        self._buckets: MutableMapping[str, MutableMapping[str, bytes]] = {}
        self._mime_types: MutableMapping[str, MutableMapping[str, str | None]] = {}

    async def ensure_bucket(
        self, bucket: str, *, region: str | None = None, create_if_missing: bool = True
    ) -> None:
        if bucket in self._buckets:
            return
        if not create_if_missing:
            raise FileNotFoundError(f"Bucket {bucket} is missing")
        self._buckets[bucket] = {}
        self._mime_types[bucket] = {}

    async def get_presigned_upload(
        self,
        *,
        bucket: str,
        key: str,
        content_type: str | None,
        expires_in: int,
        size: int | None,
        checksum_sha256: str | None,
    ) -> StoragePresignedUrl:
        await self.ensure_bucket(bucket)
        return StoragePresignedUrl(
            url=f"{self._scheme}://{bucket}/{key}",
            method="PUT",
            headers={
                "Content-Type": content_type or "application/octet-stream",
                "X-Memory-Expires-In": str(expires_in),
                "X-Memory-Checksum": checksum_sha256 or "",
                "X-Memory-Size": str(size or 0),
            },
        )

    async def get_presigned_download(
        self, *, bucket: str, key: str, expires_in: int
    ) -> StoragePresignedUrl:
        await self.ensure_bucket(bucket)
        return StoragePresignedUrl(
            url=f"{self._scheme}://{bucket}/{key}",
            method="GET",
            headers={"X-Memory-Expires-In": str(expires_in)},
        )

    async def head_object(self, *, bucket: str, key: str) -> StorageObjectRef | None:
        bucket_data = self._buckets.get(bucket)
        if not bucket_data:
            return None
        if key not in bucket_data:
            return None
        data = bucket_data[key]
        mime = self._mime_types.get(bucket, {}).get(key)
        checksum = hashlib.sha256(data).hexdigest()
        return StorageObjectRef(
            bucket=bucket,
            key=key,
            size_bytes=len(data),
            mime_type=mime,
            checksum_sha256=checksum,
        )

    async def get_object_bytes(self, *, bucket: str, key: str) -> bytes:
        bucket_data = self._buckets.get(bucket)
        if not bucket_data:
            raise FileNotFoundError(f"Bucket {bucket} is missing")
        if key not in bucket_data:
            raise FileNotFoundError(f"Object {key} not found")
        return bucket_data[key]

    async def delete_object(self, *, bucket: str, key: str) -> None:
        if bucket in self._buckets and key in self._buckets[bucket]:
            del self._buckets[bucket][key]
            self._mime_types[bucket].pop(key, None)

    async def put_object(
        self, *, bucket: str, key: str, data: bytes, content_type: str | None
    ) -> StorageObjectRef:
        await self.ensure_bucket(bucket)
        self._buckets[bucket][key] = data
        self._mime_types[bucket][key] = content_type
        checksum = hashlib.sha256(data).hexdigest()
        return StorageObjectRef(
            bucket=bucket,
            key=key,
            size_bytes=len(data),
            mime_type=content_type,
            checksum_sha256=checksum,
        )

    async def health_check(self) -> StorageProviderHealth:
        return StorageProviderHealth(status=StorageProviderStatus.HEALTHY, details={})


__all__ = ["MemoryStorageProvider"]
