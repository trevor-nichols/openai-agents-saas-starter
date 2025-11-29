"""MinIO (S3-compatible) storage provider using boto3."""

from __future__ import annotations

import asyncio
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.domain.storage import (
    MinioProviderConfig,
    StorageObjectRef,
    StoragePresignedUrl,
    StorageProviderHealth,
    StorageProviderProtocol,
    StorageProviderStatus,
)


class MinioStorageProvider(StorageProviderProtocol):
    """S3-compatible provider targeting MinIO."""

    def __init__(self, config: MinioProviderConfig) -> None:
        self._config = config
        self._client = boto3.client(
            "s3",
            endpoint_url=config.endpoint,
            aws_access_key_id=config.access_key,
            aws_secret_access_key=config.secret_key,
            region_name=config.region,
            use_ssl=config.secure,
            config=Config(signature_version="s3v4"),
        )

    async def ensure_bucket(
        self, bucket: str, *, region: str | None = None, create_if_missing: bool = True
    ) -> None:
        def _ensure() -> None:
            try:
                self._client.head_bucket(Bucket=bucket)
                return
            except ClientError as exc:
                error_code = exc.response.get("Error", {}).get("Code")
                if error_code not in ("404", "NoSuchBucket"):
                    raise
            if not create_if_missing:
                raise FileNotFoundError(f"Bucket {bucket} not found")
            create_kwargs: dict[str, Any] = {"Bucket": bucket}
            target_region = region or self._config.region
            if target_region and target_region != "us-east-1":
                create_kwargs["CreateBucketConfiguration"] = {
                    "LocationConstraint": target_region
                }
            self._client.create_bucket(**create_kwargs)

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
        params = {"Bucket": bucket, "Key": key}
        if content_type:
            params["ContentType"] = content_type
        url = await asyncio.to_thread(
            self._client.generate_presigned_url,
            ClientMethod="put_object",
            Params=params,
            ExpiresIn=expires_in,
        )
        headers = {}
        if content_type:
            headers["Content-Type"] = content_type
        if checksum_sha256:
            headers["x-amz-content-sha256"] = checksum_sha256
        if size is not None:
            headers["Content-Length"] = str(size)
        return StoragePresignedUrl(url=url, method="PUT", headers=headers)

    async def get_presigned_download(
        self, *, bucket: str, key: str, expires_in: int
    ) -> StoragePresignedUrl:
        url = await asyncio.to_thread(
            self._client.generate_presigned_url,
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        return StoragePresignedUrl(url=url, method="GET", headers={})

    async def head_object(self, *, bucket: str, key: str) -> StorageObjectRef | None:
        def _head() -> StorageObjectRef | None:
            try:
                resp = self._client.head_object(Bucket=bucket, Key=key)
            except ClientError as exc:
                if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey"):
                    return None
                raise
            return StorageObjectRef(
                bucket=bucket,
                key=key,
                size_bytes=resp.get("ContentLength"),
                mime_type=resp.get("ContentType"),
                checksum_sha256=None,
            )

        return await asyncio.to_thread(_head)

    async def delete_object(self, *, bucket: str, key: str) -> None:
        await asyncio.to_thread(self._client.delete_object, Bucket=bucket, Key=key)

    async def put_object(
        self, *, bucket: str, key: str, data: bytes, content_type: str | None
    ) -> StorageObjectRef:
        def _put() -> StorageObjectRef:
            extra: dict[str, Any] = {}
            if content_type:
                extra["ContentType"] = content_type
            self._client.put_object(Bucket=bucket, Key=key, Body=data, **extra)
            return StorageObjectRef(
                bucket=bucket,
                key=key,
                size_bytes=len(data),
                mime_type=content_type,
                checksum_sha256=None,
            )

        return await asyncio.to_thread(_put)

    async def health_check(self) -> StorageProviderHealth:
        def _check() -> StorageProviderHealth:
            try:
                self._client.list_buckets()
                return StorageProviderHealth(
                    status=StorageProviderStatus.HEALTHY,
                    details={"provider": "minio"},
                )
            except (BotoCoreError, ClientError) as exc:
                return StorageProviderHealth(
                    status=StorageProviderStatus.UNAVAILABLE,
                    details={"error": str(exc)},
                )

        return await asyncio.to_thread(_check)


__all__ = ["MinioStorageProvider"]
