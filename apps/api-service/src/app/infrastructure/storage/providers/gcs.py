"""Google Cloud Storage provider."""

from __future__ import annotations

import asyncio
import json
from datetime import timedelta
from typing import Any

from google.api_core import exceptions as gcs_exceptions
from google.cloud import storage  # type: ignore[attr-defined]
from google.oauth2 import service_account

from app.domain.storage import (
    GCSProviderConfig,
    StorageObjectRef,
    StoragePresignedUrl,
    StorageProviderHealth,
    StorageProviderProtocol,
    StorageProviderStatus,
)


class GCSStorageProvider(StorageProviderProtocol):
    """GCS-backed provider with V4 signed URLs."""

    def __init__(self, config: GCSProviderConfig) -> None:
        self._config = config
        self._client = self._build_client(config)

    def _build_client(self, config: GCSProviderConfig) -> storage.Client:
        if config.credentials_json:
            info = config.credentials_json
            if isinstance(info, str):
                try:
                    info = json.loads(info)
                except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                    raise ValueError("GCS_CREDENTIALS_JSON must be valid JSON") from exc
            creds = service_account.Credentials.from_service_account_info(info)
            return storage.Client(project=config.project_id, credentials=creds)
        if config.credentials_path:
            creds = service_account.Credentials.from_service_account_file(config.credentials_path)
            return storage.Client(project=config.project_id, credentials=creds)
        return storage.Client(project=config.project_id)

    async def ensure_bucket(
        self, bucket: str, *, region: str | None = None, create_if_missing: bool = True
    ) -> None:
        def _ensure() -> None:
            bkt = self._client.bucket(bucket)
            if bkt.exists():
                return
            if not create_if_missing:
                raise FileNotFoundError(f"GCS bucket {bucket} not found")
            bkt.location = region or "US"
            bkt.iam_configuration.uniform_bucket_level_access_enabled = (
                self._config.uniform_access
            )
            bkt.create()

        await asyncio.to_thread(_ensure)

    async def get_presigned_upload(
        self,
        *,
        bucket: str,
        key: str,
        content_type: str | None,
        expires_in: int,
        size: int | None,
        checksum_sha256: str | None,
    ) -> StoragePresignedUrl:
        def _sign() -> StoragePresignedUrl:
            blob = self._client.bucket(bucket).blob(key)
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(seconds=expires_in),
                method="PUT",
                content_type=content_type,
                credentials=blob.client._credentials,
                service_account_email=self._config.signing_email,
            )
            headers: dict[str, str] = {}
            if content_type:
                headers["Content-Type"] = content_type
            if size is not None:
                headers["Content-Length"] = str(size)
            if checksum_sha256:
                headers["x-goog-content-sha256"] = checksum_sha256
            return StoragePresignedUrl(url=url, method="PUT", headers=headers)

        return await asyncio.to_thread(_sign)

    async def get_presigned_download(
        self, *, bucket: str, key: str, expires_in: int
    ) -> StoragePresignedUrl:
        def _sign() -> StoragePresignedUrl:
            blob = self._client.bucket(bucket).blob(key)
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(seconds=expires_in),
                method="GET",
                credentials=blob.client._credentials,
                service_account_email=self._config.signing_email,
            )
            return StoragePresignedUrl(url=url, method="GET", headers={})

        return await asyncio.to_thread(_sign)

    async def head_object(self, *, bucket: str, key: str) -> StorageObjectRef | None:
        def _head() -> StorageObjectRef | None:
            blob = self._client.bucket(bucket).blob(key)
            try:
                blob.reload()
            except gcs_exceptions.NotFound:
                return None
            return StorageObjectRef(
                bucket=bucket,
                key=key,
                size_bytes=blob.size,
                mime_type=blob.content_type,
                checksum_sha256=blob.crc32c,  # crc32c available; sha256 not exposed
            )

        return await asyncio.to_thread(_head)

    async def get_object_bytes(self, *, bucket: str, key: str) -> bytes:
        def _get() -> bytes:
            blob = self._client.bucket(bucket).blob(key)
            try:
                return blob.download_as_bytes()
            except gcs_exceptions.NotFound as exc:
                raise FileNotFoundError(f"Object {key} not found") from exc

        return await asyncio.to_thread(_get)

    async def delete_object(self, *, bucket: str, key: str) -> None:
        def _delete() -> None:
            blob = self._client.bucket(bucket).blob(key)
            try:
                blob.delete()
            except gcs_exceptions.NotFound:
                return

        await asyncio.to_thread(_delete)

    async def put_object(
        self, *, bucket: str, key: str, data: bytes, content_type: str | None
    ) -> StorageObjectRef:
        def _put() -> StorageObjectRef:
            blob = self._client.bucket(bucket).blob(key)
            kwargs: dict[str, Any] = {}
            if content_type:
                kwargs["content_type"] = content_type
            blob.upload_from_string(data, **kwargs)
            blob.reload()
            return StorageObjectRef(
                bucket=bucket,
                key=key,
                size_bytes=blob.size,
                mime_type=blob.content_type,
                checksum_sha256=blob.crc32c,
            )

        return await asyncio.to_thread(_put)

    async def health_check(self) -> StorageProviderHealth:
        def _check() -> StorageProviderHealth:
            try:
                self._client.list_buckets(page_size=1)
                return StorageProviderHealth(
                    status=StorageProviderStatus.HEALTHY,
                    details={"provider": "gcs"},
                )
            except gcs_exceptions.GoogleAPIError as exc:
                return StorageProviderHealth(
                    status=StorageProviderStatus.UNAVAILABLE,
                    details={"error": str(exc)},
                )

        return await asyncio.to_thread(_check)


__all__ = ["GCSStorageProvider"]
