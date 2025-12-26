"""Shared storage-provider contracts used by both backend and CLI."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Protocol, runtime_checkable


class StorageProviderLiteral(StrEnum):
    """Enumerates supported object storage providers."""

    MINIO = "minio"
    GCS = "gcs"
    S3 = "s3"
    AZURE_BLOB = "azure_blob"
    MEMORY = "memory"  # test/default provider; never used in production


class StorageProviderStatus(StrEnum):
    """Health status states exposed by providers."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass(slots=True)
class StorageProviderHealth:
    """Surface provider readiness diagnostics."""

    status: StorageProviderStatus
    details: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class StoragePresignedUrl:
    """Represents a presigned request."""

    url: str
    method: str
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class StorageObjectRef:
    """Lightweight descriptor for an object."""

    bucket: str
    key: str
    size_bytes: int | None = None
    mime_type: str | None = None
    checksum_sha256: str | None = None
    id: uuid.UUID | None = None
    filename: str | None = None
    status: str | None = None
    created_at: datetime | None = None
    conversation_id: uuid.UUID | None = None
    agent_key: str | None = None


@dataclass(slots=True)
class MinioProviderConfig:
    """Resolved MinIO configuration shared across surfaces."""

    endpoint: str | None
    access_key: str | None
    secret_key: str | None
    region: str | None
    secure: bool


@dataclass(slots=True)
class GCSProviderConfig:
    """Resolved GCS configuration shared across surfaces."""

    project_id: str | None
    bucket: str | None
    credentials_json: dict[str, object] | str | None
    credentials_path: str | None
    signing_email: str | None
    uniform_access: bool


@dataclass(slots=True)
class S3ProviderConfig:
    """Resolved S3 configuration shared across surfaces."""

    region: str | None
    bucket: str | None
    endpoint_url: str | None
    force_path_style: bool


@dataclass(slots=True)
class AzureBlobProviderConfig:
    """Resolved Azure Blob configuration shared across surfaces."""

    account_url: str | None
    container: str | None
    connection_string: str | None


@runtime_checkable
class StorageProviderProtocol(Protocol):
    """Async contract every storage provider must satisfy."""

    async def ensure_bucket(
        self, bucket: str, *, region: str | None = None, create_if_missing: bool = True
    ) -> None: ...

    async def get_presigned_upload(
        self,
        *,
        bucket: str,
        key: str,
        content_type: str | None,
        expires_in: int,
        size: int | None,
        checksum_sha256: str | None,
    ) -> StoragePresignedUrl: ...

    async def get_presigned_download(
        self, *, bucket: str, key: str, expires_in: int
    ) -> StoragePresignedUrl: ...

    async def head_object(self, *, bucket: str, key: str) -> StorageObjectRef | None: ...

    async def get_object_bytes(self, *, bucket: str, key: str) -> bytes: ...

    async def delete_object(self, *, bucket: str, key: str) -> None: ...

    async def put_object(
        self, *, bucket: str, key: str, data: bytes, content_type: str | None
    ) -> StorageObjectRef: ...

    async def health_check(self) -> StorageProviderHealth: ...


__all__ = [
    "AzureBlobProviderConfig",
    "GCSProviderConfig",
    "MinioProviderConfig",
    "S3ProviderConfig",
    "StorageObjectRef",
    "StoragePresignedUrl",
    "StorageProviderHealth",
    "StorageProviderLiteral",
    "StorageProviderProtocol",
    "StorageProviderStatus",
]
