from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.domain.storage import AzureBlobProviderConfig, S3ProviderConfig
from app.infrastructure.storage import registry


@dataclass
class _DummySettings:
    s3_settings: S3ProviderConfig
    azure_blob_settings: AzureBlobProviderConfig


def _settings_for_s3(*, bucket: str | None) -> _DummySettings:
    return _DummySettings(
        s3_settings=S3ProviderConfig(
            region=None,
            bucket=bucket,
            endpoint_url=None,
            force_path_style=False,
        ),
        azure_blob_settings=AzureBlobProviderConfig(
            account_url=None,
            container=None,
            connection_string=None,
        ),
    )


def _settings_for_azure(
    *,
    container: str | None,
    account_url: str | None,
    connection_string: str | None,
) -> _DummySettings:
    return _DummySettings(
        s3_settings=S3ProviderConfig(
            region=None,
            bucket=None,
            endpoint_url=None,
            force_path_style=False,
        ),
        azure_blob_settings=AzureBlobProviderConfig(
            account_url=account_url,
            container=container,
            connection_string=connection_string,
        ),
    )


def test_build_s3_provider_requires_bucket():
    settings = _settings_for_s3(bucket=None)
    with pytest.raises(RuntimeError, match="S3_BUCKET"):
        registry._build_s3_provider(settings)


def test_build_s3_provider_accepts_bucket(monkeypatch):
    settings = _settings_for_s3(bucket="assets")

    def _fake_provider(config: S3ProviderConfig) -> str:
        return f"s3:{config.bucket}"  # pragma: no cover - trivial stub

    monkeypatch.setattr(registry, "S3StorageProvider", _fake_provider)
    assert registry._build_s3_provider(settings) == "s3:assets"


def test_build_azure_provider_requires_container():
    settings = _settings_for_azure(
        container=None,
        account_url="https://acct.blob.core.windows.net",
        connection_string=None,
    )
    with pytest.raises(RuntimeError, match="AZURE_BLOB_CONTAINER"):
        registry._build_azure_blob_provider(settings)


def test_build_azure_provider_requires_connection_info():
    settings = _settings_for_azure(container="assets", account_url=None, connection_string=None)
    with pytest.raises(RuntimeError, match="AZURE_BLOB_CONNECTION_STRING"):
        registry._build_azure_blob_provider(settings)


def test_build_azure_provider_accepts_connection_string(monkeypatch):
    settings = _settings_for_azure(
        container="assets",
        account_url=None,
        connection_string="DefaultEndpointsProtocol=https;AccountName=test;AccountKey=abc;EndpointSuffix=core.windows.net",
    )

    def _fake_provider(config: AzureBlobProviderConfig) -> str:
        return f"azure:{config.container}"  # pragma: no cover - trivial stub

    monkeypatch.setattr(registry, "AzureBlobStorageProvider", _fake_provider)
    assert registry._build_azure_blob_provider(settings) == "azure:assets"
