"""Object storage provider settings (MinIO, S3, Azure Blob, GCS, memory)."""

from __future__ import annotations

from pydantic import BaseModel, Field
from starter_contracts.storage.models import (
    AzureBlobProviderConfig,
    GCSProviderConfig,
    MinioProviderConfig,
    S3ProviderConfig,
    StorageProviderLiteral,
)


class StorageSettingsMixin(BaseModel):
    storage_provider: StorageProviderLiteral = Field(
        default=StorageProviderLiteral.MEMORY,
        alias="STORAGE_PROVIDER",
        description=(
            "Which storage provider implementation to use "
            "(minio, gcs, s3, azure_blob, memory)."
        ),
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
            "application/gzip",
            "application/octet-stream",
            "application/pdf",
            "application/zip",
            "application/x-tar",
            "application/x-sh",
            "application/xml",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/msword",
            "application/typescript",
            "application/csv",
            "text/plain",
            "text/csv",
            "text/markdown",
            "text/css",
            "text/x-python",
            "text/x-c",
            "text/x-c++",
            "text/x-csharp",
            "text/x-java",
            "text/x-php",
            "text/x-ruby",
            "text/x-tex",
            "text/x-javascript",
            "text/javascript",
            "text/html",
            "image/png",
            "image/jpeg",
            "image/webp",
            "image/gif",
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
        alias="GCP_PROJECT_ID",
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

    # S3
    s3_region: str | None = Field(
        default=None,
        description="AWS region for S3 operations (optional; falls back to SDK defaults).",
    )
    s3_bucket: str | None = Field(
        default=None,
        description="S3 bucket name for storage operations.",
    )
    s3_endpoint_url: str | None = Field(
        default=None,
        description="Optional custom S3 endpoint URL (leave blank for AWS).",
    )
    s3_force_path_style: bool = Field(
        default=False,
        description="Force path-style addressing for S3-compatible endpoints.",
    )

    # Azure Blob
    azure_blob_account_url: str | None = Field(
        default=None,
        description="Azure Blob account URL (https://<account>.blob.core.windows.net).",
    )
    azure_blob_container: str | None = Field(
        default=None,
        description="Azure Blob container name for storage operations.",
    )
    azure_blob_connection_string: str | None = Field(
        default=None,
        description="Azure Blob connection string (optional, overrides account URL auth).",
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

    @property
    def s3_settings(self) -> S3ProviderConfig:
        return S3ProviderConfig(
            region=self.s3_region,
            bucket=self.s3_bucket,
            endpoint_url=self.s3_endpoint_url,
            force_path_style=self.s3_force_path_style,
        )

    @property
    def azure_blob_settings(self) -> AzureBlobProviderConfig:
        return AzureBlobProviderConfig(
            account_url=self.azure_blob_account_url,
            container=self.azure_blob_container,
            connection_string=self.azure_blob_connection_string,
        )


__all__ = ["StorageSettingsMixin"]
