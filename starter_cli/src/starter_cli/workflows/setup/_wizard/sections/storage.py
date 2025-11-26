from __future__ import annotations

from starter_contracts.storage.models import StorageProviderLiteral

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIError

from ...inputs import InputProvider
from ...context import WizardContext


def run(context: WizardContext, provider: InputProvider) -> None:
    console.section(
        "Storage",
        "Choose object storage backend (MinIO self-hosted or Google Cloud Storage).",
    )

    current = context.current("STORAGE_PROVIDER") or (
        StorageProviderLiteral.MINIO.value if context.profile == "local" else StorageProviderLiteral.GCS.value
    )
    choice = provider.prompt_choice(
        key="STORAGE_PROVIDER",
        prompt="Select storage provider",
        choices=[
            StorageProviderLiteral.MINIO.value,
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
    elif provider_literal == StorageProviderLiteral.GCS:
        _configure_gcs(context, provider)


def _configure_minio(context: WizardContext, provider: InputProvider) -> None:
    default_endpoint = context.current("MINIO_ENDPOINT") or (
        "http://localhost:9000" if context.profile == "local" else ""
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
        default=context.current("MINIO_ACCESS_KEY") or ("minioadmin" if context.profile == "local" else ""),
        required=True,
    )
    secret_key = provider.prompt_secret(
        key="MINIO_SECRET_KEY",
        prompt="MinIO secret key",
        existing=context.current("MINIO_SECRET_KEY"),
        required=True,
    )
    region = provider.prompt_string(
        key="MINIO_REGION",
        prompt="MinIO region (optional)",
        default=context.current("MINIO_REGION") or "",
        required=False,
    )
    secure_default = context.profile != "local"
    secure = provider.prompt_bool(
        key="MINIO_SECURE",
        prompt="Use HTTPS for MinIO?",
        default=context.current_bool("MINIO_SECURE", secure_default),
    )

    context.set_backend("MINIO_ENDPOINT", endpoint)
    context.set_backend("MINIO_ACCESS_KEY", access_key, mask=False)
    context.set_backend("MINIO_SECRET_KEY", secret_key, mask=True)
    context.set_backend("MINIO_REGION", region)
    context.set_backend_bool("MINIO_SECURE", secure)


def _configure_gcs(context: WizardContext, provider: InputProvider) -> None:
    project_id = provider.prompt_string(
        key="GCS_PROJECT_ID",
        prompt="GCS project id",
        default=context.current("GCS_PROJECT_ID") or "",
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

    context.set_backend("GCS_PROJECT_ID", project_id)
    context.set_backend("GCS_BUCKET", bucket)
    context.set_backend("GCS_CREDENTIALS_PATH", creds_path)
    context.set_backend("GCS_CREDENTIALS_JSON", creds_json, mask=True)
    context.set_backend("GCS_SIGNING_EMAIL", signing_email)
    context.set_backend_bool("GCS_UNIFORM_ACCESS", uniform_access)


__all__ = ["run"]
