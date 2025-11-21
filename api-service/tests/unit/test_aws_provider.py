from __future__ import annotations

import pytest

from app.domain.secrets import SecretPurpose
from app.infrastructure.secrets.aws_provider import (
    AWSSecretsManagerProvider,
)


class _StubSMClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def get_secret_value(self, secret_id: str):
        self.calls.append(secret_id)
        if secret_id == "arn:signing":
            return "aws-secret-value"
        return "other"

    def describe_secret(self, secret_id: str):
        self.calls.append(f"describe:{secret_id}")
        return {"ARN": secret_id}


@pytest.mark.asyncio
async def test_aws_provider_sign_and_verify() -> None:
    client = _StubSMClient()
    provider = AWSSecretsManagerProvider(
        client=client,
        signing_secret_arn="arn:signing",
        cache_ttl_seconds=30,
    )

    payload = b'{"account":"ci"}'
    signed = await provider.sign(payload, purpose=SecretPurpose.GENERIC)
    assert signed.algorithm == "aws-sm-hmac-sha256"
    assert await provider.verify(payload, signed.signature, purpose=SecretPurpose.GENERIC)

    # Ensure caching reuses secret without extra AWS calls.
    await provider.sign(payload, purpose=SecretPurpose.GENERIC)
    assert client.calls.count("arn:signing") == 1
