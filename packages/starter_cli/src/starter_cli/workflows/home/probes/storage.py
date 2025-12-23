from __future__ import annotations

from starter_contracts.storage.models import StorageProviderLiteral

from starter_cli.core.status_models import ProbeResult, ProbeState
from starter_cli.workflows.home.probes.registry import ProbeContext
from starter_cli.workflows.home.probes.util import simple_result


def storage_probe(ctx: ProbeContext) -> ProbeResult:
    provider_value = ctx.env.get("STORAGE_PROVIDER", "").lower()
    try:
        provider = StorageProviderLiteral(provider_value)
    except ValueError:
        return simple_result(
            name="storage",
            success=False,
            detail="STORAGE_PROVIDER missing or invalid (expected minio, s3, azure_blob, or gcs)",
            remediation="Set STORAGE_PROVIDER via the setup wizard.",
        )

    if provider == StorageProviderLiteral.MINIO:
        missing = [
            key
            for key in ("MINIO_ENDPOINT", "MINIO_ACCESS_KEY", "MINIO_SECRET_KEY")
            if not ctx.env.get(key)
        ]
        if missing:
            return simple_result(
                name="storage",
                success=False,
                detail=f"Missing MinIO env vars: {', '.join(missing)}",
                remediation="Populate the MinIO endpoint/access/secret and rerun the wizard.",
            )
        return simple_result(
            name="storage",
            success=True,
            detail="MinIO configured",
        )

    if provider == StorageProviderLiteral.GCS:
        missing = [key for key in ("GCS_BUCKET",) if not ctx.env.get(key)]
        if missing:
            return simple_result(
                name="storage",
                success=False,
                detail=f"Missing GCS env vars: {', '.join(missing)}",
                remediation="Set GCS_BUCKET and credentials path/JSON.",
            )
        return simple_result(name="storage", success=True, detail="GCS configured")

    if provider == StorageProviderLiteral.S3:
        missing = [key for key in ("S3_BUCKET",) if not ctx.env.get(key)]
        if missing:
            return simple_result(
                name="storage",
                success=False,
                detail=f"Missing S3 env vars: {', '.join(missing)}",
                remediation="Set S3_BUCKET and optional S3_REGION in the wizard.",
            )
        return simple_result(name="storage", success=True, detail="S3 configured")

    if provider == StorageProviderLiteral.AZURE_BLOB:
        missing = [key for key in ("AZURE_BLOB_CONTAINER",) if not ctx.env.get(key)]
        if missing:
            return simple_result(
                name="storage",
                success=False,
                detail=f"Missing Azure Blob env vars: {', '.join(missing)}",
                remediation="Set AZURE_BLOB_CONTAINER and connection string/account URL.",
            )
        has_auth = bool(
            ctx.env.get("AZURE_BLOB_CONNECTION_STRING")
            or ctx.env.get("AZURE_BLOB_ACCOUNT_URL")
        )
        if not has_auth:
            return simple_result(
                name="storage",
                success=False,
                detail="Azure Blob auth missing (connection string or account URL required).",
                remediation="Set AZURE_BLOB_CONNECTION_STRING or AZURE_BLOB_ACCOUNT_URL.",
            )
        return simple_result(name="storage", success=True, detail="Azure Blob configured")

    return ProbeResult(
        name="storage",
        state=ProbeState.SKIPPED,
        detail="Storage provider not configured",
    )


__all__ = ["storage_probe"]
