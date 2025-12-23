"""Backend-facing aliases for shared storage provider models."""

from starter_contracts.storage.models import (
    AzureBlobProviderConfig,
    GCSProviderConfig,
    MinioProviderConfig,
    S3ProviderConfig,
    StorageObjectRef,
    StoragePresignedUrl,
    StorageProviderHealth,
    StorageProviderLiteral,
    StorageProviderProtocol,
    StorageProviderStatus,
)

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
