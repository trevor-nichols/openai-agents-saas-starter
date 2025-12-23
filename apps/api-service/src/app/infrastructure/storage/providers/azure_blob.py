"""Azure Blob storage provider."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse

from azure.core.exceptions import AzureError, ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import (
    BlobSasPermissions,
    BlobServiceClient,
    ContentSettings,
    generate_blob_sas,
)

from app.domain.storage import (
    AzureBlobProviderConfig,
    StorageObjectRef,
    StoragePresignedUrl,
    StorageProviderHealth,
    StorageProviderProtocol,
    StorageProviderStatus,
)


class AzureBlobStorageProvider(StorageProviderProtocol):
    """Azure Blob provider using SAS URLs for uploads/downloads."""

    def __init__(self, config: AzureBlobProviderConfig) -> None:
        self._config = config
        self._account_name: str | None = None
        self._account_key: str | None = None
        self._credential = None

        if config.connection_string:
            self._account_name, self._account_key = _parse_connection_string(
                config.connection_string
            )
            self._service_client = BlobServiceClient.from_connection_string(
                config.connection_string
            )
        else:
            if not config.account_url:
                raise RuntimeError(
                    "AZURE_BLOB_ACCOUNT_URL is required when no connection string is provided"
                )
            self._account_name = _account_name_from_url(config.account_url)
            self._credential = DefaultAzureCredential(
                exclude_interactive_browser_credential=True
            )
            self._service_client = BlobServiceClient(
                account_url=config.account_url, credential=self._credential
            )

    async def ensure_bucket(
        self, bucket: str, *, region: str | None = None, create_if_missing: bool = True
    ) -> None:
        def _ensure() -> None:
            container = self._service_client.get_container_client(bucket)
            try:
                container.get_container_properties()
                return
            except ResourceNotFoundError as exc:
                if not create_if_missing:
                    raise FileNotFoundError(f"Container {bucket} not found") from exc
                container.create_container()

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
        sas = await self._generate_sas(
            bucket=bucket,
            key=key,
            permissions=BlobSasPermissions(write=True, create=True),
            expires_in=expires_in,
        )
        blob_client = self._service_client.get_blob_client(container=bucket, blob=key)
        url = f"{blob_client.url}?{sas}"
        headers: dict[str, str] = {"x-ms-blob-type": "BlockBlob"}
        if content_type:
            headers["Content-Type"] = content_type
        if size is not None:
            headers["Content-Length"] = str(size)
        return StoragePresignedUrl(url=url, method="PUT", headers=headers)

    async def get_presigned_download(
        self, *, bucket: str, key: str, expires_in: int
    ) -> StoragePresignedUrl:
        sas = await self._generate_sas(
            bucket=bucket,
            key=key,
            permissions=BlobSasPermissions(read=True),
            expires_in=expires_in,
        )
        blob_client = self._service_client.get_blob_client(container=bucket, blob=key)
        url = f"{blob_client.url}?{sas}"
        return StoragePresignedUrl(url=url, method="GET", headers={})

    async def head_object(self, *, bucket: str, key: str) -> StorageObjectRef | None:
        def _head() -> StorageObjectRef | None:
            blob_client = self._service_client.get_blob_client(container=bucket, blob=key)
            try:
                props = blob_client.get_blob_properties()
            except ResourceNotFoundError:
                return None
            return StorageObjectRef(
                bucket=bucket,
                key=key,
                size_bytes=getattr(props, "size", None),
                mime_type=getattr(getattr(props, "content_settings", None), "content_type", None),
                checksum_sha256=None,
            )

        return await asyncio.to_thread(_head)

    async def get_object_bytes(self, *, bucket: str, key: str) -> bytes:
        def _get() -> bytes:
            blob_client = self._service_client.get_blob_client(container=bucket, blob=key)
            try:
                downloader = blob_client.download_blob()
            except ResourceNotFoundError as exc:
                raise FileNotFoundError(f"Object {key} not found") from exc
            return downloader.readall()

        return await asyncio.to_thread(_get)

    async def delete_object(self, *, bucket: str, key: str) -> None:
        blob_client = self._service_client.get_blob_client(container=bucket, blob=key)
        await asyncio.to_thread(blob_client.delete_blob, delete_snapshots="include")

    async def put_object(
        self, *, bucket: str, key: str, data: bytes, content_type: str | None
    ) -> StorageObjectRef:
        def _put() -> StorageObjectRef:
            blob_client = self._service_client.get_blob_client(container=bucket, blob=key)
            content_settings = ContentSettings(content_type=content_type)
            blob_client.upload_blob(
                data,
                overwrite=True,
                content_settings=content_settings,
            )
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
                self._service_client.get_account_information()
                return StorageProviderHealth(
                    status=StorageProviderStatus.HEALTHY,
                    details={"provider": "azure_blob"},
                )
            except AzureError as exc:
                return StorageProviderHealth(
                    status=StorageProviderStatus.UNAVAILABLE,
                    details={"error": str(exc)},
                )

        return await asyncio.to_thread(_check)

    async def _generate_sas(
        self,
        *,
        bucket: str,
        key: str,
        permissions: BlobSasPermissions,
        expires_in: int,
    ) -> str:
        if not self._account_name:
            raise RuntimeError("Azure storage account name is unavailable")
        account_name = self._account_name
        assert account_name is not None

        expiry = datetime.now(UTC) + timedelta(seconds=expires_in)
        start = datetime.now(UTC) - timedelta(minutes=5)

        def _sas() -> str:
            if self._account_key:
                return generate_blob_sas(
                    account_name=account_name,
                    container_name=bucket,
                    blob_name=key,
                    account_key=self._account_key,
                    permission=permissions,
                    expiry=expiry,
                )

            if not self._credential:
                raise RuntimeError("Azure credential is required for SAS generation")

            delegation_key = self._service_client.get_user_delegation_key(start, expiry)
            return generate_blob_sas(
                account_name=account_name,
                container_name=bucket,
                blob_name=key,
                user_delegation_key=delegation_key,
                permission=permissions,
                expiry=expiry,
            )

        return await asyncio.to_thread(_sas)


def _parse_connection_string(connection_string: str) -> tuple[str | None, str | None]:
    parts: dict[str, str] = {}
    for item in connection_string.split(";"):
        if not item:
            continue
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        parts[key.strip()] = value.strip()
    return parts.get("AccountName"), parts.get("AccountKey")


def _account_name_from_url(account_url: str) -> str:
    parsed = urlparse(account_url)
    host = parsed.netloc
    if not host:
        raise RuntimeError("Invalid AZURE_BLOB_ACCOUNT_URL")
    return host.split(".")[0]


__all__ = ["AzureBlobStorageProvider"]
