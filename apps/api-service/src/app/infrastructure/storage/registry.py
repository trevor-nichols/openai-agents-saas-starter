"""Provider registry used to build the configured StorageProvider."""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping

from app.core.config import Settings, get_settings
from app.domain.storage import (
    GCSProviderConfig,
    MinioProviderConfig,
    StorageProviderLiteral,
    StorageProviderProtocol,
)
from app.infrastructure.storage.providers.gcs import GCSStorageProvider
from app.infrastructure.storage.providers.memory import MemoryStorageProvider
from app.infrastructure.storage.providers.minio import MinioStorageProvider

ProviderFactory = Callable[[Settings], StorageProviderProtocol]
logger = logging.getLogger(__name__)


def _build_registry() -> Mapping[StorageProviderLiteral, ProviderFactory]:
    return {
        StorageProviderLiteral.MEMORY: lambda _settings: MemoryStorageProvider(),
        StorageProviderLiteral.MINIO: _build_minio_provider,
        StorageProviderLiteral.GCS: _build_gcs_provider,
    }


def _build_minio_provider(settings: Settings) -> StorageProviderProtocol:
    cfg: MinioProviderConfig = settings.minio_settings
    if not cfg.endpoint:
        raise RuntimeError("MINIO_ENDPOINT is required when STORAGE_PROVIDER=minio")
    return MinioStorageProvider(cfg)


def _build_gcs_provider(settings: Settings) -> StorageProviderProtocol:
    cfg: GCSProviderConfig = settings.gcs_settings
    if not cfg.bucket:
        raise RuntimeError("GCS_BUCKET is required when STORAGE_PROVIDER=gcs")
    if not (cfg.credentials_json or cfg.credentials_path):
        # ADC allowed; warn to aid operators
        logger.warning(
            "Using Application Default Credentials for GCS; set GCS_CREDENTIALS_JSON or "
            "GCS_CREDENTIALS_PATH to be explicit."
        )
    return GCSStorageProvider(cfg)


_PROVIDER_CACHE: StorageProviderProtocol | None = None
_PROVIDER_KEY: StorageProviderLiteral | None = None


def reset_storage_provider_cache() -> None:
    """Clear cached storage provider (test helper)."""

    global _PROVIDER_CACHE, _PROVIDER_KEY
    _PROVIDER_CACHE = None
    _PROVIDER_KEY = None


def get_storage_provider(settings: Settings | None = None) -> StorageProviderProtocol:
    """Return (and cache) the configured StorageProvider implementation."""

    global _PROVIDER_CACHE, _PROVIDER_KEY
    settings = settings or get_settings()
    provider_key = settings.storage_provider

    if _PROVIDER_CACHE and provider_key == _PROVIDER_KEY:
        return _PROVIDER_CACHE

    registry = _build_registry()
    try:
        factory = registry[provider_key]
    except KeyError as exc:  # pragma: no cover - defensive
        raise RuntimeError(f"Storage provider {provider_key!r} is not registered.") from exc

    provider = factory(settings)
    _PROVIDER_CACHE = provider
    _PROVIDER_KEY = provider_key
    logger.info("Initialized storage provider", extra={"storage_provider": provider_key.value})
    return provider


__all__ = ["get_storage_provider", "reset_storage_provider_cache"]
