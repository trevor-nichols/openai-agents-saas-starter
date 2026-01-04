"""SecretProvider implementation backed by GCP Secret Manager."""

from __future__ import annotations

import hmac
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

from anyio import to_thread

from app.core.settings import Settings
from app.domain.secrets import (
    SecretProviderHealth,
    SecretProviderProtocol,
    SecretProviderStatus,
    SecretPurpose,
    SecretScope,
    SignedPayload,
)

from .gcp_client import GCPSecretManagerClient, GCPSecretManagerError


@dataclass
class _CacheEntry:
    value: str
    expires_at: float


@dataclass
class GCPSecretManagerProvider(SecretProviderProtocol):
    client: GCPSecretManagerClient | Any
    signing_secret_name: str
    cache_ttl_seconds: int = 60
    _cache: dict[str, _CacheEntry] = field(default_factory=dict)

    async def get_secret(self, key: str, *, scope: SecretScope | None = None) -> str:
        _ = scope
        return await self._get_or_fetch(key)

    async def get_secrets(
        self,
        keys: Sequence[str],
        *,
        scope: SecretScope | None = None,
    ) -> dict[str, str]:
        _ = scope
        results: dict[str, str] = {}
        for key in keys:
            results[key] = await self._get_or_fetch(key)
        return results

    async def sign(self, payload: bytes, *, purpose: SecretPurpose) -> SignedPayload:
        key = await self._get_signing_secret()
        signature = hmac.new(key, payload, sha256).hexdigest()
        return SignedPayload(
            signature=signature,
            algorithm="gcp-sm-hmac-sha256",
            metadata={},
        )

    async def verify(
        self,
        payload: bytes,
        signature: str,
        *,
        purpose: SecretPurpose,
    ) -> bool:
        key = await self._get_signing_secret()
        expected = hmac.new(key, payload, sha256).hexdigest()
        return hmac.compare_digest(signature, expected)

    async def health_check(self) -> SecretProviderHealth:
        try:
            await self._get_signing_secret(force_refresh=True)
        except GCPSecretManagerError as exc:
            return SecretProviderHealth(
                status=SecretProviderStatus.UNAVAILABLE,
                details={"error": str(exc)},
            )
        return SecretProviderHealth(status=SecretProviderStatus.HEALTHY, details={})

    async def _get_or_fetch(self, secret_name: str, *, force_refresh: bool = False) -> str:
        cached = self._cache.get(secret_name)
        now = time.time()
        if not force_refresh and cached and cached.expires_at >= now:
            return cached.value
        value = await to_thread.run_sync(self.client.get_secret_value, secret_name)
        self._cache[secret_name] = _CacheEntry(
            value=value,
            expires_at=now + max(1, self.cache_ttl_seconds),
        )
        return value

    async def _get_signing_secret(self, *, force_refresh: bool = False) -> bytes:
        cache_key = f"signing::{self.signing_secret_name}"
        if not force_refresh:
            cached = self._cache.get(cache_key)
            if cached and cached.expires_at >= time.time():
                return cached.value.encode("utf-8")
        value = await self._get_or_fetch(self.signing_secret_name, force_refresh=force_refresh)
        self._cache[cache_key] = _CacheEntry(
            value=value,
            expires_at=time.time() + max(1, self.cache_ttl_seconds),
        )
        return value.encode("utf-8")


def build_gcp_secret_provider(settings: Settings) -> SecretProviderProtocol:
    config = settings.gcp_settings
    if not config.signing_secret_name:
        raise GCPSecretManagerError("GCP_SM_SIGNING_SECRET_NAME must be set.")
    if not config.project_id and not config.signing_secret_name.startswith("projects/"):
        raise GCPSecretManagerError(
            "GCP_SM_PROJECT_ID or GCP_PROJECT_ID must be set when secret name "
            "is not fully qualified."
        )

    client = GCPSecretManagerClient(project_id=config.project_id or None)
    return GCPSecretManagerProvider(
        client=client,
        signing_secret_name=config.signing_secret_name,
        cache_ttl_seconds=config.cache_ttl_seconds,
    )


__all__ = ["GCPSecretManagerProvider", "build_gcp_secret_provider"]
