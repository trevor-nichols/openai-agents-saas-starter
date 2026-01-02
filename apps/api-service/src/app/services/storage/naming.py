"""Shared storage naming helpers."""

from __future__ import annotations

import re
from uuid import UUID

from app.core.settings import Settings
from app.domain.storage import StorageProviderLiteral

_SAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def bucket_name(settings: Settings, tenant_id: UUID) -> str:
    if settings.storage_provider == StorageProviderLiteral.GCS and settings.gcs_bucket:
        return settings.gcs_bucket
    if settings.storage_provider == StorageProviderLiteral.S3 and settings.s3_bucket:
        return settings.s3_bucket
    if (
        settings.storage_provider == StorageProviderLiteral.AZURE_BLOB
        and settings.azure_blob_container
    ):
        return settings.azure_blob_container
    prefix = settings.storage_bucket_prefix or "agent-data"
    tenant_token = str(tenant_id).replace("-", "")
    return f"{prefix}-{tenant_token}"


def bucket_region(settings: Settings) -> str | None:
    if settings.storage_provider == StorageProviderLiteral.MINIO:
        return settings.minio_region
    if settings.storage_provider == StorageProviderLiteral.S3:
        return settings.s3_region
    return None


def should_auto_create_bucket(settings: Settings) -> bool:
    return settings.storage_provider not in {
        StorageProviderLiteral.GCS,
        StorageProviderLiteral.S3,
        StorageProviderLiteral.AZURE_BLOB,
    }


def safe_filename(filename: str) -> str:
    cleaned = _SAFE_CHARS.sub("-", filename).strip("-")
    return cleaned or "file"


__all__ = [
    "bucket_name",
    "bucket_region",
    "safe_filename",
    "should_auto_create_bucket",
]
