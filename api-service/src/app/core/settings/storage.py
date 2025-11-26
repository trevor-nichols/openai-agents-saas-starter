"""Object storage provider settings (MinIO, GCS, memory)."""
# ruff: noqa: I001

from __future__ import annotations

from pydantic import BaseModel, Field

from starter_contracts.storage.models import (
    GCSProviderConfig,
    MinioProviderConfig,
    StorageProviderLiteral,
)


class StorageSettingsMixin(BaseModel):
    storage_provider: StorageProviderLiteral = Field(
        default=StorageProviderLiteral.MEMORY,
        alias="STORAGE_PROVIDER",
        description="Which storage provider implementation to use (minio, gcs, memory).",
    )
    storage_bucket_prefix: str | None = Field(
        default="agent-data",
        description="Prefix used when creating tenant buckets/prefixes.",
    )
    storage_signed_url_ttl_seconds: int = Field(
        default=900,
        ge=60,
        description="TTL (seconds) for presigned URLs returned to clients.",
    )
    storage_max_file_mb: int = Field(
        default=512,
        ge=1,
        description="Maximum upload size enforced by the service (MB).",
    )
    storage_allowed_mime_types: list[str] = Field(
        default_factory=lambda: [
            "application/json",
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/msword",
            "text/plain",
            "text/markdown",
            "text/x-python",
            "text/x-javascript",
            "text/javascript",
            "text/html",
        ],
        description="Allowed MIME types for uploaded objects.",
    )

    # MinIO
    minio_endpoint: str | None = Field(
        default=None,
        description="MinIO endpoint (http(s)://host:port). Required when storage_provider=minio.",
    )
    minio_access_key: str | None = Field(default=None, description="MinIO access key.")
    minio_secret_key: str | None = Field(default=None, description="MinIO secret key.")
    minio_region: str | None = Field(default=None, description="MinIO region (optional).")
    minio_secure: bool = Field(
        default=True,
        description="Use HTTPS when connecting to MinIO.",
    )

    # GCS
    gcs_project_id: str | None = Field(
        default=None,
        description="GCP project ID for GCS operations.",
    )
    gcs_bucket: str | None = Field(
        default=None,
        description="Default bucket name when using GCS provider.",
    )
    gcs_credentials_json: str | None = Field(
        default=None,
        description=(
            "Inline JSON credentials for GCS (service account). "
            "Optional if using ADC or credentials path."
        ),
    )
    gcs_credentials_path: str | None = Field(
        default=None,
        description="Path to GCS credentials JSON file.",
    )
    gcs_signing_email: str | None = Field(
        default=None,
        description="Service account email used for V4 signed URLs (GCS).",
    )
    gcs_uniform_access: bool = Field(
        default=True,
        description="Assume uniform bucket-level access (UBLA) is enabled.",
    )

    @property
    def minio_settings(self) -> MinioProviderConfig:
        return MinioProviderConfig(
            endpoint=self.minio_endpoint,
            access_key=self.minio_access_key,
            secret_key=self.minio_secret_key,
            region=self.minio_region,
            secure=self.minio_secure,
        )

    @property
    def gcs_settings(self) -> GCSProviderConfig:
        return GCSProviderConfig(
            project_id=self.gcs_project_id,
            bucket=self.gcs_bucket,
            credentials_json=self.gcs_credentials_json,
            credentials_path=self.gcs_credentials_path,
            signing_email=self.gcs_signing_email,
            uniform_access=self.gcs_uniform_access,
        )


__all__ = ["StorageSettingsMixin"]
