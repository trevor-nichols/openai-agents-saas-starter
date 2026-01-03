from __future__ import annotations

import pytest

from app.core.settings import Settings
from app.domain.secrets import SecretPurpose
from app.infrastructure.secrets.gcp_client import GCPSecretManagerError
from app.infrastructure.secrets.gcp_provider import GCPSecretManagerProvider
from app.infrastructure.secrets.gcp_provider import build_gcp_secret_provider


class _StubGCPClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def get_secret_value(self, secret_id: str):
        self.calls.append(secret_id)
        if secret_id == "signing-secret":
            return "gcp-secret-value"
        return "other"


@pytest.mark.asyncio
async def test_gcp_provider_sign_and_verify() -> None:
    client = _StubGCPClient()
    provider = GCPSecretManagerProvider(
        client=client,
        signing_secret_name="signing-secret",
        cache_ttl_seconds=30,
    )

    payload = b'{"account":"ci"}'
    signed = await provider.sign(payload, purpose=SecretPurpose.GENERIC)
    assert signed.algorithm == "gcp-sm-hmac-sha256"
    assert await provider.verify(payload, signed.signature, purpose=SecretPurpose.GENERIC)

    # Ensure caching reuses secret without extra calls.
    await provider.sign(payload, purpose=SecretPurpose.GENERIC)
    assert client.calls.count("signing-secret") == 1


@pytest.mark.asyncio
async def test_gcp_provider_health_check_force_refresh_hits_provider() -> None:
    client = _StubGCPClient()
    provider = GCPSecretManagerProvider(
        client=client,
        signing_secret_name="signing-secret",
        cache_ttl_seconds=30,
    )

    payload = b'{"account":"ci"}'
    await provider.sign(payload, purpose=SecretPurpose.GENERIC)
    assert client.calls.count("signing-secret") == 1

    await provider.health_check()
    assert client.calls.count("signing-secret") == 2


def test_gcp_provider_requires_signing_secret_name() -> None:
    settings = Settings(_env_file=None)
    settings.gcp_sm_project_id = "demo-project"
    settings.gcp_sm_signing_secret_name = None

    with pytest.raises(GCPSecretManagerError, match="GCP_SM_SIGNING_SECRET_NAME"):
        build_gcp_secret_provider(settings)


def test_gcp_provider_requires_project_id_for_unqualified_secret() -> None:
    settings = Settings(_env_file=None)
    settings.gcp_sm_project_id = None
    settings.gcp_sm_signing_secret_name = "auth-signing-secret"

    with pytest.raises(GCPSecretManagerError, match="GCP_SM_PROJECT_ID"):
        build_gcp_secret_provider(settings)
