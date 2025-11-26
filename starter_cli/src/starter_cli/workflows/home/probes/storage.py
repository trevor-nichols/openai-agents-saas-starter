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
            detail="STORAGE_PROVIDER missing or invalid (expected minio or gcs)",
            remediation="Set STORAGE_PROVIDER to minio or gcs via the setup wizard.",
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

    return ProbeResult(
        name="storage",
        state=ProbeState.SKIPPED,
        detail="Storage provider not configured",
    )


__all__ = ["storage_probe"]
