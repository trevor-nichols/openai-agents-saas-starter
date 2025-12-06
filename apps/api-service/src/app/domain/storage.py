"""Backend-facing aliases for shared storage provider models."""

from starter_contracts.storage.models import (
    GCSProviderConfig,
    MinioProviderConfig,
    StorageObjectRef,
    StoragePresignedUrl,
    StorageProviderHealth,
    StorageProviderLiteral,
    StorageProviderProtocol,
    StorageProviderStatus,
)

__all__ = [
    "GCSProviderConfig",
    "MinioProviderConfig",
    "StorageObjectRef",
    "StoragePresignedUrl",
    "StorageProviderHealth",
    "StorageProviderLiteral",
    "StorageProviderProtocol",
    "StorageProviderStatus",
]
