from __future__ import annotations

from starter_contracts.storage.models import StorageProviderLiteral

from starter_console.core import CLIError

from ...inputs import InputProvider
from ..context import WizardContext


def run(context: WizardContext, provider: InputProvider) -> None:
    context.console.section(
        "Storage",
        "Choose object storage backend (MinIO, S3, Azure Blob, or Google Cloud Storage).",
    )

    current = context.current("STORAGE_PROVIDER") or (
        StorageProviderLiteral.MINIO.value
        if context.profile == "demo"
        else StorageProviderLiteral.S3.value
    )
    choice = provider.prompt_choice(
        key="STORAGE_PROVIDER",
        prompt="Select storage provider",
        choices=[
            StorageProviderLiteral.MINIO.value,
            StorageProviderLiteral.S3.value,
            StorageProviderLiteral.AZURE_BLOB.value,
            StorageProviderLiteral.GCS.value,
        ],
        default=current,
    )
    try:
        provider_literal = StorageProviderLiteral(choice)
    except ValueError as exc:  # pragma: no cover - user input guarded
        raise CLIError(f"Invalid storage provider '{choice}'.") from exc

    bucket_prefix = provider.prompt_string(
        key="STORAGE_BUCKET_PREFIX",
        prompt="Bucket/prefix base (storage bucket prefix)",
        default=context.current("STORAGE_BUCKET_PREFIX") or "agent-data",
        required=True,
    )
    context.set_backend("STORAGE_PROVIDER", provider_literal.value)
    context.set_backend("STORAGE_BUCKET_PREFIX", bucket_prefix)

    if provider_literal == StorageProviderLiteral.MINIO:
        _configure_minio(context, provider)
    elif provider_literal == StorageProviderLiteral.S3:
        _configure_s3(context, provider)
    elif provider_literal == StorageProviderLiteral.AZURE_BLOB:
        _configure_azure_blob(context, provider)
    elif provider_literal == StorageProviderLiteral.GCS:
        _configure_gcs(context, provider)

    _configure_image_defaults(context, provider)


def _configure_minio(context: WizardContext, provider: InputProvider) -> None:
    default_endpoint = context.current("MINIO_ENDPOINT") or (
        "http://localhost:9000" if context.profile == "demo" else ""
    )
    endpoint = provider.prompt_string(
        key="MINIO_ENDPOINT",
        prompt="MinIO endpoint (http(s)://host:port)",
        default=default_endpoint,
        required=True,
    )
    access_key = provider.prompt_string(
        key="MINIO_ACCESS_KEY",
        prompt="MinIO access key",
        default=context.current("MINIO_ACCESS_KEY")
        or ("minioadmin" if context.profile == "demo" else ""),
        required=True,
    )
    default_secret = context.current("MINIO_SECRET_KEY") or (
        "minioadmin" if context.profile == "demo" else ""
    )
    secret_key = provider.prompt_secret(
        key="MINIO_SECRET_KEY",
        prompt="MinIO secret key",
        existing=default_secret or context.current("MINIO_SECRET_KEY"),
        required=not bool(default_secret),
    )
    region = provider.prompt_string(
        key="MINIO_REGION",
        prompt="MinIO region (optional)",
        default=context.current("MINIO_REGION") or "",
        required=False,
    )
    secure_default = context.profile != "demo"
    secure = provider.prompt_bool(
        key="MINIO_SECURE",
        prompt="Use HTTPS for MinIO?",
        default=context.current_bool("MINIO_SECURE", secure_default),
    )

    context.set_backend("MINIO_ENDPOINT", endpoint)
    context.set_backend("MINIO_ACCESS_KEY", access_key, mask=False)
    context.set_backend("MINIO_SECRET_KEY", secret_key or default_secret, mask=True)
    context.set_backend("MINIO_REGION", region)
    context.set_backend_bool("MINIO_SECURE", secure)


def _configure_gcs(context: WizardContext, provider: InputProvider) -> None:
    project_id = provider.prompt_string(
        key="GCP_PROJECT_ID",
        prompt="GCP project id",
        default=context.current("GCP_PROJECT_ID") or "",
        required=True,
    )
    bucket = provider.prompt_string(
        key="GCS_BUCKET",
        prompt="GCS bucket name",
        default=context.current("GCS_BUCKET") or "",
        required=True,
    )
    creds_path = provider.prompt_string(
        key="GCS_CREDENTIALS_PATH",
        prompt="Path to GCS service account JSON (blank = ADC)",
        default=context.current("GCS_CREDENTIALS_PATH") or "",
        required=False,
    )
    creds_json = provider.prompt_secret(
        key="GCS_CREDENTIALS_JSON",
        prompt="Inline GCS credentials JSON (blank to skip)",
        existing=context.current("GCS_CREDENTIALS_JSON"),
        required=False,
    )
    signing_email = provider.prompt_string(
        key="GCS_SIGNING_EMAIL",
        prompt="Service account email for signed URLs (optional)",
        default=context.current("GCS_SIGNING_EMAIL") or "",
        required=False,
    )
    uniform_access = provider.prompt_bool(
        key="GCS_UNIFORM_ACCESS",
        prompt="Bucket uses Uniform Access (UBLA)?",
        default=context.current_bool("GCS_UNIFORM_ACCESS", True),
    )

    context.set_backend("GCP_PROJECT_ID", project_id)
    context.set_backend("GCS_BUCKET", bucket)
    context.set_backend("GCS_CREDENTIALS_PATH", creds_path)
    context.set_backend("GCS_CREDENTIALS_JSON", creds_json, mask=True)
    context.set_backend("GCS_SIGNING_EMAIL", signing_email)
    context.set_backend_bool("GCS_UNIFORM_ACCESS", uniform_access)


def _configure_s3(context: WizardContext, provider: InputProvider) -> None:
    bucket = provider.prompt_string(
        key="S3_BUCKET",
        prompt="S3 bucket name",
        default=context.current("S3_BUCKET") or "",
        required=True,
    )
    region = provider.prompt_string(
        key="S3_REGION",
        prompt="S3 region (blank = SDK default)",
        default=context.current("S3_REGION") or "",
        required=False,
    )
    endpoint = provider.prompt_string(
        key="S3_ENDPOINT_URL",
        prompt="Custom S3 endpoint URL (blank = AWS)",
        default=context.current("S3_ENDPOINT_URL") or "",
        required=False,
    )
    force_path_style = provider.prompt_bool(
        key="S3_FORCE_PATH_STYLE",
        prompt="Force path-style addressing?",
        default=context.current_bool("S3_FORCE_PATH_STYLE", False),
    )

    context.set_backend("S3_BUCKET", bucket)
    context.set_backend("S3_REGION", region)
    context.set_backend("S3_ENDPOINT_URL", endpoint)
    context.set_backend_bool("S3_FORCE_PATH_STYLE", force_path_style)


def _configure_azure_blob(context: WizardContext, provider: InputProvider) -> None:
    container = provider.prompt_string(
        key="AZURE_BLOB_CONTAINER",
        prompt="Azure Blob container name",
        default=context.current("AZURE_BLOB_CONTAINER") or "",
        required=True,
    )
    connection_string = provider.prompt_secret(
        key="AZURE_BLOB_CONNECTION_STRING",
        prompt="Azure Blob connection string (blank to use account URL + managed identity)",
        existing=context.current("AZURE_BLOB_CONNECTION_STRING"),
        required=False,
    )
    account_url = provider.prompt_string(
        key="AZURE_BLOB_ACCOUNT_URL",
        prompt="Azure Blob account URL (required if no connection string)",
        default=context.current("AZURE_BLOB_ACCOUNT_URL") or "",
        required=not bool(connection_string),
    )
    if not connection_string and not account_url:
        raise CLIError(
            "AZURE_BLOB_ACCOUNT_URL is required when no connection string is provided."
        )

    context.set_backend("AZURE_BLOB_CONTAINER", container)
    if connection_string:
        context.set_backend("AZURE_BLOB_CONNECTION_STRING", connection_string, mask=True)
    context.set_backend("AZURE_BLOB_ACCOUNT_URL", account_url)


def _configure_image_defaults(context: WizardContext, provider: InputProvider) -> None:
    context.console.note(
        "Generated images will be stored in the configured provider; defaults below can be"
        " overridden per-agent via tool_configs.",
        topic="image-generation",
    )

    size = provider.prompt_string(
        key="IMAGE_DEFAULT_SIZE",
        prompt="Default image size (auto, 1024x1024, 1024x1536, 1536x1024)",
        default=context.current("IMAGE_DEFAULT_SIZE") or "1024x1024",
        required=True,
    )
    quality = provider.prompt_string(
        key="IMAGE_DEFAULT_QUALITY",
        prompt="Default image quality (auto, low, medium, high)",
        default=context.current("IMAGE_DEFAULT_QUALITY") or "high",
        required=True,
    )
    fmt = provider.prompt_string(
        key="IMAGE_DEFAULT_FORMAT",
        prompt="Default image format (png, jpeg, webp)",
        default=context.current("IMAGE_DEFAULT_FORMAT") or "png",
        required=True,
    )
    background = provider.prompt_string(
        key="IMAGE_DEFAULT_BACKGROUND",
        prompt="Default background (auto, opaque, transparent)",
        default=context.current("IMAGE_DEFAULT_BACKGROUND") or "auto",
        required=True,
    )
    compression = provider.prompt_string(
        key="IMAGE_DEFAULT_COMPRESSION",
        prompt="Default compression 0-100 (blank = provider chooses)",
        default=context.current("IMAGE_DEFAULT_COMPRESSION") or "",
        required=False,
    )
    max_mb = provider.prompt_string(
        key="IMAGE_OUTPUT_MAX_MB",
        prompt="Max decoded image size (MB)",
        default=context.current("IMAGE_OUTPUT_MAX_MB") or "6",
        required=True,
    )
    partial = provider.prompt_string(
        key="IMAGE_MAX_PARTIAL_IMAGES",
        prompt="Max partial images to stream (0-3)",
        default=context.current("IMAGE_MAX_PARTIAL_IMAGES") or "2",
        required=True,
    )

    context.set_backend("IMAGE_DEFAULT_SIZE", size)
    context.set_backend("IMAGE_DEFAULT_QUALITY", quality)
    context.set_backend("IMAGE_DEFAULT_FORMAT", fmt)
    context.set_backend("IMAGE_DEFAULT_BACKGROUND", background)
    if compression:
        context.set_backend("IMAGE_DEFAULT_COMPRESSION", compression)
    context.set_backend("IMAGE_OUTPUT_MAX_MB", max_mb)
    context.set_backend("IMAGE_MAX_PARTIAL_IMAGES", partial)


__all__ = ["run"]
