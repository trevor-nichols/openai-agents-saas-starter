from __future__ import annotations

from azure.core.exceptions import AzureError

from app.domain.storage import AzureBlobProviderConfig, StorageProviderStatus
from app.infrastructure.storage.providers import azure_blob


class _StubBlobServiceClient:
    def __init__(self, *, should_fail: bool = False) -> None:
        self._should_fail = should_fail
        self.account_info_calls = 0

    def get_account_information(self):
        self.account_info_calls += 1
        if self._should_fail:
            raise AzureError("boom")
        return {}


class _StubClientFactory:
    def __init__(self, stub: _StubBlobServiceClient) -> None:
        self._stub = stub

    def from_connection_string(self, _connection: str) -> _StubBlobServiceClient:
        return self._stub


async def test_health_check_uses_account_information(monkeypatch):
    stub = _StubBlobServiceClient()
    monkeypatch.setattr(azure_blob, "BlobServiceClient", _StubClientFactory(stub))

    config = AzureBlobProviderConfig(
        account_url=None,
        container="assets",
        connection_string="AccountName=test;AccountKey=abc;EndpointSuffix=core.windows.net",
    )
    provider = azure_blob.AzureBlobStorageProvider(config)

    health = await provider.health_check()

    assert stub.account_info_calls == 1
    assert health.status is StorageProviderStatus.HEALTHY


async def test_health_check_reports_unavailable_on_error(monkeypatch):
    stub = _StubBlobServiceClient(should_fail=True)
    monkeypatch.setattr(azure_blob, "BlobServiceClient", _StubClientFactory(stub))

    config = AzureBlobProviderConfig(
        account_url=None,
        container="assets",
        connection_string="AccountName=test;AccountKey=abc;EndpointSuffix=core.windows.net",
    )
    provider = azure_blob.AzureBlobStorageProvider(config)

    health = await provider.health_check()

    assert stub.account_info_calls == 1
    assert health.status is StorageProviderStatus.UNAVAILABLE
