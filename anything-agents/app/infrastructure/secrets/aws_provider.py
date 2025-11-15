"""SecretProvider implementation backed by AWS Secrets Manager."""

from __future__ import annotations

import hmac
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

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

from .aws_client import AWSSecretsManagerClient, AWSSecretsManagerError


@dataclass
class _CacheEntry:
    value: str
    expires_at: float


@dataclass
class AWSSecretsManagerProvider(SecretProviderProtocol):
    client: AWSSecretsManagerClient | Any
    signing_secret_arn: str
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
        results = {}
        for key in keys:
            results[key] = await self._get_or_fetch(key)
        return results

    async def sign(self, payload: bytes, *, purpose: SecretPurpose) -> SignedPayload:
        key = await self._get_signing_secret()
        signature = hmac.new(key, payload, sha256).hexdigest()
        return SignedPayload(
            signature=signature,
            algorithm="aws-sm-hmac-sha256",
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
            await to_thread.run_sync(
                self.client.describe_secret,
                self.signing_secret_arn,
            )
        except AWSSecretsManagerError as exc:
            return SecretProviderHealth(
                status=SecretProviderStatus.UNAVAILABLE,
                details={"error": str(exc)},
            )
        return SecretProviderHealth(status=SecretProviderStatus.HEALTHY, details={})

    async def _get_or_fetch(self, secret_id: str) -> str:
        cached = self._cache.get(secret_id)
        if cached and cached.expires_at >= time.time():
            return cached.value
        value = await to_thread.run_sync(
            self.client.get_secret_value,
            secret_id,
        )
        self._cache[secret_id] = _CacheEntry(
            value=value,
            expires_at=time.time() + max(1, self.cache_ttl_seconds),
        )
        return value

    async def _get_signing_secret(self) -> bytes:
        value = await self._get_or_fetch(self.signing_secret_arn)
        return value.encode("utf-8")


def build_aws_secret_provider(settings: Settings) -> SecretProviderProtocol:
    config = settings.aws_settings
    if not config.region:
        raise AWSSecretsManagerError("AWS_REGION must be set for aws_sm provider.")
    if not config.signing_secret_arn:
        raise AWSSecretsManagerError("AWS_SM_SIGNING_SECRET_ARN must be set.")

    client = AWSSecretsManagerClient(
        region=config.region,
        profile=config.profile,
        access_key_id=config.access_key_id,
        secret_access_key=config.secret_access_key,
        session_token=config.session_token,
    )

    return AWSSecretsManagerProvider(
        client=client,
        signing_secret_arn=config.signing_secret_arn,
        cache_ttl_seconds=config.cache_ttl_seconds,
    )


__all__ = ["AWSSecretsManagerProvider", "build_aws_secret_provider"]
