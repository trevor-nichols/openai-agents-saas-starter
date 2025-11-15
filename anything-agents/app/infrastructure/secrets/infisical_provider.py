"""SecretProvider implementation backed by Infisical."""

from __future__ import annotations

import hmac
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from hashlib import sha256

from anyio import to_thread

from app.core.config import Settings
from app.domain.secrets import (
    SecretProviderHealth,
    SecretProviderProtocol,
    SecretProviderStatus,
    SecretPurpose,
    SecretScope,
    SignedPayload,
)

from .infisical_client import InfisicalAPIClient, InfisicalAPIError


@dataclass
class _CacheEntry:
    value: str
    expires_at: float


@dataclass
class InfisicalSecretProvider(SecretProviderProtocol):
    client: InfisicalAPIClient
    signing_secret_name: str
    cache_ttl_seconds: int = 60
    _cache: dict[str, _CacheEntry] = field(default_factory=dict)

    async def get_secret(self, key: str, *, scope: SecretScope | None = None) -> str:
        _ = scope
        value = self._get_cached_secret(key)
        if value is not None:
            return value
        value = await self._fetch_secret(key)
        self._cache_secret(key, value)
        return value

    async def get_secrets(
        self,
        keys: Sequence[str],
        *,
        scope: SecretScope | None = None,
    ) -> dict[str, str]:
        _ = scope
        results: dict[str, str] = {}
        missing: list[str] = []
        for key in keys:
            cached = self._get_cached_secret(key)
            if cached is not None:
                results[key] = cached
            else:
                missing.append(key)

        for key in missing:
            value = await self._fetch_secret(key)
            self._cache_secret(key, value)
            results[key] = value
        return results

    async def sign(self, payload: bytes, *, purpose: SecretPurpose) -> SignedPayload:
        secret = await self._ensure_signing_secret()
        signature = hmac.new(secret, payload, sha256).hexdigest()
        return SignedPayload(
            signature=signature,
            algorithm="infisical-hmac-sha256",
            metadata={},
        )

    async def verify(
        self,
        payload: bytes,
        signature: str,
        *,
        purpose: SecretPurpose,
    ) -> bool:
        secret = await self._ensure_signing_secret()
        expected = hmac.new(secret, payload, sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    async def health_check(self) -> SecretProviderHealth:
        try:
            await self._ensure_signing_secret(force_refresh=True)
        except InfisicalAPIError as exc:
            return SecretProviderHealth(
                status=SecretProviderStatus.UNAVAILABLE,
                details={"error": str(exc)},
            )
        except Exception as exc:  # pragma: no cover - defensive
            return SecretProviderHealth(
                status=SecretProviderStatus.DEGRADED,
                details={"error": str(exc)},
            )
        return SecretProviderHealth(status=SecretProviderStatus.HEALTHY, details={})

    async def _fetch_secret(self, key: str) -> str:
        value = await to_thread.run_sync(self.client.get_secret, key)
        if value is None:
            raise InfisicalAPIError(f"Secret {key!r} was not found.")
        return value

    def _cache_secret(self, key: str, value: str) -> None:
        ttl = max(1, self.cache_ttl_seconds)
        self._cache[key] = _CacheEntry(value=value, expires_at=time.time() + ttl)

    def _get_cached_secret(self, key: str) -> str | None:
        entry = self._cache.get(key)
        if not entry:
            return None
        if entry.expires_at < time.time():
            self._cache.pop(key, None)
            return None
        return entry.value

    async def _ensure_signing_secret(self, *, force_refresh: bool = False) -> bytes:
        cache_key = f"signing::{self.signing_secret_name}"
        if not force_refresh:
            cached = self._get_cached_secret(cache_key)
            if cached is not None:
                return cached.encode("utf-8")

        secret_value = await self._fetch_secret(self.signing_secret_name)
        self._cache_secret(cache_key, secret_value)
        return secret_value.encode("utf-8")


def build_infisical_secret_provider(settings: Settings) -> SecretProviderProtocol:
    config = settings.infisical_settings
    if not (config.base_url and config.service_token and config.project_id and config.environment):
        raise InfisicalAPIError(
            "Infisical base URL, service token, project ID, and environment must be configured."
        )

    client = InfisicalAPIClient(
        base_url=config.base_url,
        service_token=config.service_token,
        project_id=config.project_id,
        environment=config.environment,
        secret_path=config.secret_path or "/",
        ca_bundle_path=config.ca_bundle_path,
    )

    return InfisicalSecretProvider(
        client=client,
        signing_secret_name=config.signing_secret_name,
        cache_ttl_seconds=config.cache_ttl_seconds,
    )


__all__ = ["InfisicalSecretProvider", "build_infisical_secret_provider"]
