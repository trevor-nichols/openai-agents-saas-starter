from __future__ import annotations

import pytest

from app.domain.secrets import SecretPurpose
from app.infrastructure.secrets.azure_provider import AzureKeyVaultProvider


class _StubKVClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def get_secret(self, name: str) -> str:
        self.calls.append(name)
        if name == "signing":
            return "azure-secret"
        return "value"


@pytest.mark.asyncio
async def test_azure_provider_sign_verify() -> None:
    client = _StubKVClient()
    provider = AzureKeyVaultProvider(
        client=client,
        signing_secret_name="signing",
        cache_ttl_seconds=60,
    )
    payload = b'{"example":1}'
    signed = await provider.sign(payload, purpose=SecretPurpose.GENERIC)
    assert signed.algorithm == "azure-kv-hmac-sha256"
    assert await provider.verify(payload, signed.signature, purpose=SecretPurpose.GENERIC)
    await provider.sign(payload, purpose=SecretPurpose.GENERIC)
    assert client.calls.count("signing") == 1


@pytest.mark.asyncio
async def test_azure_provider_health_check_force_refresh_hits_provider() -> None:
    client = _StubKVClient()
    provider = AzureKeyVaultProvider(
        client=client,
        signing_secret_name="signing",
        cache_ttl_seconds=60,
    )
    payload = b'{"example":1}'
    await provider.sign(payload, purpose=SecretPurpose.GENERIC)
    assert client.calls.count("signing") == 1

    await provider.health_check()
    assert client.calls.count("signing") == 2
