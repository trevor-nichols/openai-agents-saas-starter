from __future__ import annotations

import boto3

from app.domain.storage import S3ProviderConfig, StorageProviderStatus
from app.infrastructure.storage.providers.s3 import S3StorageProvider


class _StubClient:
    def __init__(self) -> None:
        self.head_bucket_called = False
        self.head_bucket_bucket: str | None = None
        self.list_buckets_called = False

    def head_bucket(self, *, Bucket: str) -> None:  # noqa: N802 - boto3 style
        self.head_bucket_called = True
        self.head_bucket_bucket = Bucket

    def list_buckets(self) -> None:  # pragma: no cover - should not be called
        self.list_buckets_called = True
        raise AssertionError("list_buckets should not be used for health checks")


async def test_health_check_uses_head_bucket(monkeypatch):
    stub = _StubClient()

    def _client(service_name: str, **_kwargs):  # noqa: ANN001 - boto3 signature
        assert service_name == "s3"
        return stub

    monkeypatch.setattr(boto3, "client", _client)

    config = S3ProviderConfig(
        region=None,
        bucket="demo-assets",
        endpoint_url=None,
        force_path_style=False,
    )
    provider = S3StorageProvider(config)

    health = await provider.health_check()

    assert stub.head_bucket_called is True
    assert stub.head_bucket_bucket == "demo-assets"
    assert stub.list_buckets_called is False
    assert health.status is StorageProviderStatus.HEALTHY
    assert health.details.get("bucket") == "demo-assets"
