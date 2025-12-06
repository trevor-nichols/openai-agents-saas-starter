"""Service layer for storage orchestration."""
# ruff: noqa: I001

from __future__ import annotations

import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass

from app.core.settings import Settings
from app.domain.storage import (
    StorageObjectRef,
    StoragePresignedUrl,
    StorageProviderLiteral,
    StorageProviderProtocol,
)
from app.observability import metrics
from app.infrastructure.persistence.storage.postgres import StorageRepository
from app.infrastructure.storage.registry import get_storage_provider
from app.services.activity import activity_service

_SAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(slots=True)
class PresignedUpload:
    object_id: uuid.UUID
    upload_url: str
    method: str
    headers: dict[str, str]
    bucket: str
    object_key: str


class StorageService:
    """Coordinates storage provider operations with persistence and guardrails."""

    def __init__(
        self,
        session_factory,
        settings_provider: Callable[[], Settings],
        provider_resolver: Callable[[Settings], StorageProviderProtocol] = get_storage_provider,
        repository: StorageRepository | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._settings_provider = settings_provider
        self._provider_resolver = provider_resolver
        self._repository = repository or StorageRepository(session_factory)

    async def create_presigned_upload(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID | None,
        filename: str,
        mime_type: str | None,
        size_bytes: int | None,
        agent_key: str | None = None,
        conversation_id: uuid.UUID | None = None,
        metadata: dict[str, object] | None = None,
    ) -> PresignedUpload:
        settings = self._settings_provider()
        self._enforce_size(size_bytes, settings)
        self._enforce_mime(mime_type, settings)

        provider = self._provider_resolver(settings)
        bucket_name = self._bucket_name(settings, tenant_id)
        await provider.ensure_bucket(
            bucket_name,
            region=settings.minio_region,
            create_if_missing=settings.storage_provider != StorageProviderLiteral.GCS,
        )
        bucket = await self._repository.get_or_create_bucket(
            tenant_id=tenant_id,
            provider=settings.storage_provider.value,
            bucket_name=bucket_name,
            region=settings.minio_region,
            prefix=settings.storage_bucket_prefix,
        )

        object_id = uuid.uuid4()
        safe_name = self._safe_filename(filename)
        object_key = f"{tenant_id}/{object_id}/{safe_name}"

        # Provider presign
        upload = await provider.get_presigned_upload(
            bucket=bucket_name,
            key=object_key,
            content_type=mime_type,
            expires_in=settings.storage_signed_url_ttl_seconds,
            size=size_bytes,
            checksum_sha256=None,
        )

        # Persist metadata
        await self._repository.create_object(
            tenant_id=tenant_id,
            bucket=bucket,
            object_id=object_id,
            object_key=object_key,
            filename=filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            checksum_sha256=None,
            status="pending_upload",
            created_by_user_id=user_id,
            agent_key=agent_key,
            conversation_id=conversation_id,
            metadata_json=metadata or {},
            expires_at=None,
        )

        try:
            await activity_service.record(
                tenant_id=str(tenant_id),
                action="storage.file.uploaded",
                actor_id=str(user_id) if user_id else None,
                actor_type="user" if user_id else "system",
                object_type="storage_object",
                object_id=str(object_id),
                source="api",
                metadata={"object_id": str(object_id), "bucket": bucket_name},
            )
        except Exception:  # pragma: no cover - best effort
            pass

        metrics.observe_storage_operation(
            operation="presign_upload",
            provider=settings.storage_provider.value,
            result="success",
            duration_seconds=0.0,
        )

        return PresignedUpload(
            object_id=object_id,
            upload_url=upload.url,
            method=upload.method,
            headers=upload.headers,
            bucket=bucket_name,
            object_key=object_key,
        )

    async def get_presigned_download(
        self, *, tenant_id: uuid.UUID, object_id: uuid.UUID
    ) -> tuple[StoragePresignedUrl, StorageObjectRef]:
        settings = self._settings_provider()
        provider = self._provider_resolver(settings)
        obj = await self._repository.get_object_for_tenant(tenant_id=tenant_id, object_id=object_id)
        if obj is None or obj.deleted_at is not None:
            raise FileNotFoundError("Object not found")
        url = await provider.get_presigned_download(
            bucket=obj.bucket.bucket_name,
            key=obj.object_key,
            expires_in=settings.storage_signed_url_ttl_seconds,
        )
        metrics.observe_storage_operation(
            operation="presign_download",
            provider=settings.storage_provider.value,
            result="success",
            duration_seconds=0.0,
        )
        return url, StorageObjectRef(
            id=obj.id,
            bucket=obj.bucket.bucket_name,
            key=obj.object_key,
            size_bytes=obj.size_bytes,
            mime_type=obj.mime_type,
            filename=obj.filename,
            status=obj.status,
            created_at=obj.created_at,
            conversation_id=obj.conversation_id,
            agent_key=obj.agent_key,
            checksum_sha256=obj.checksum_sha256,
        )

    async def list_objects(
        self,
        *,
        tenant_id: uuid.UUID,
        limit: int,
        offset: int,
        conversation_id: uuid.UUID | None = None,
    ) -> list[StorageObjectRef]:
        objects = await self._repository.list_objects(
            tenant_id=tenant_id, limit=limit, offset=offset, conversation_id=conversation_id
        )
        results: list[StorageObjectRef] = []
        for obj in objects:
            results.append(
                StorageObjectRef(
                    id=obj.id,
                    bucket=obj.bucket.bucket_name,
                    key=obj.object_key,
                    size_bytes=obj.size_bytes,
                    mime_type=obj.mime_type,
                    checksum_sha256=obj.checksum_sha256,
                    filename=obj.filename,
                    status=obj.status,
                    created_at=obj.created_at,
                    conversation_id=obj.conversation_id,
                    agent_key=obj.agent_key,
                )
            )
        metrics.observe_storage_operation(
            operation="list_objects",
            provider=self._settings_provider().storage_provider.value,
            result="success",
            duration_seconds=0.0,
        )
        return results

    async def delete_object(self, *, tenant_id: uuid.UUID, object_id: uuid.UUID) -> None:
        settings = self._settings_provider()
        provider = self._provider_resolver(settings)
        obj = await self._repository.get_object_for_tenant(tenant_id=tenant_id, object_id=object_id)
        if obj is None or obj.deleted_at is not None:
            return
        try:
            await provider.delete_object(bucket=obj.bucket.bucket_name, key=obj.object_key)
        finally:
            await self._repository.mark_deleted(object_id=obj.id)
        metrics.observe_storage_operation(
            operation="delete_object",
            provider=settings.storage_provider.value,
            result="success",
            duration_seconds=0.0,
        )
        try:
            await activity_service.record(
                tenant_id=str(tenant_id),
                action="storage.file.deleted",
                actor_id=str(obj.created_by_user_id) if obj.created_by_user_id else None,
                actor_type="user" if obj.created_by_user_id else "system",
                object_type="storage_object",
                object_id=str(object_id),
                source="api",
                metadata={"object_id": str(object_id), "bucket": obj.bucket.bucket_name},
            )
        except Exception:  # pragma: no cover - best effort
            pass

    async def put_object(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID | None,
        data: bytes,
        filename: str,
        mime_type: str | None,
        agent_key: str | None = None,
        conversation_id: uuid.UUID | None = None,
        metadata: dict[str, object] | None = None,
    ) -> StorageObjectRef:
        """Store a small object directly and persist metadata.

        Intended for generated assets (e.g., images) where we already have bytes
        server-side and want to avoid presign/roundtrip.
        """

        size_bytes = len(data)
        settings = self._settings_provider()
        self._enforce_size(size_bytes, settings)
        self._enforce_mime(mime_type, settings)

        provider = self._provider_resolver(settings)
        bucket_name = self._bucket_name(settings, tenant_id)
        await provider.ensure_bucket(
            bucket_name,
            region=settings.minio_region,
            create_if_missing=settings.storage_provider != StorageProviderLiteral.GCS,
        )
        bucket = await self._repository.get_or_create_bucket(
            tenant_id=tenant_id,
            provider=settings.storage_provider.value,
            bucket_name=bucket_name,
            region=settings.minio_region,
            prefix=settings.storage_bucket_prefix,
        )

        object_id = uuid.uuid4()
        safe_name = self._safe_filename(filename)
        object_key = f"{tenant_id}/{object_id}/{safe_name}"

        obj_ref = await provider.put_object(
            bucket=bucket_name,
            key=object_key,
            data=data,
            content_type=mime_type,
        )

        await self._repository.create_object(
            tenant_id=tenant_id,
            bucket=bucket,
            object_id=object_id,
            object_key=object_key,
            filename=filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            checksum_sha256=
            obj_ref.checksum_sha256 if hasattr(obj_ref, "checksum_sha256") else None,
            status="ready",
            created_by_user_id=user_id,
            agent_key=agent_key,
            conversation_id=conversation_id,
            metadata_json=metadata or {},
            expires_at=None,
        )

        metrics.observe_storage_operation(
            operation="put_object",
            provider=settings.storage_provider.value,
            result="success",
            duration_seconds=0.0,
        )

        return StorageObjectRef(
            id=object_id,
            bucket=bucket_name,
            key=object_key,
            size_bytes=size_bytes,
            mime_type=mime_type,
            filename=filename,
            status="ready",
            created_at=obj_ref.created_at if hasattr(obj_ref, "created_at") else None,
            conversation_id=conversation_id,
            agent_key=agent_key,
            checksum_sha256=
            obj_ref.checksum_sha256 if hasattr(obj_ref, "checksum_sha256") else None,
        )

    def _enforce_size(self, size_bytes: int | None, settings: Settings) -> None:
        if size_bytes is None:
            raise ValueError("File size is required")
        max_bytes = settings.storage_max_file_mb * 1024 * 1024
        if size_bytes > max_bytes:
            raise ValueError("File size exceeds allowed limit")

    def _enforce_mime(self, mime_type: str | None, settings: Settings) -> None:
        if mime_type is None:
            raise ValueError("MIME type is required")
        allowed = set(settings.storage_allowed_mime_types)
        if mime_type not in allowed:
            raise ValueError("MIME type is not allowed")

    def _bucket_name(self, settings: Settings, tenant_id: uuid.UUID) -> str:
        if (
            settings.storage_provider == StorageProviderLiteral.GCS
            and settings.gcs_bucket
        ):
            return settings.gcs_bucket
        prefix = settings.storage_bucket_prefix or "agent-data"
        tenant_token = str(tenant_id).replace("-", "")
        return f"{prefix}-{tenant_token}"

    def signed_url_ttl(self) -> int:
        return self._settings_provider().storage_signed_url_ttl_seconds

    async def health_check(self) -> dict[str, str]:
        settings = self._settings_provider()
        provider = self._provider_resolver(settings)
        health = await provider.health_check()
        return {
            "status": health.status.value,
            **health.details,
        }

    def _safe_filename(self, filename: str) -> str:
        cleaned = _SAFE_CHARS.sub("-", filename).strip("-")
        return cleaned or "file"
