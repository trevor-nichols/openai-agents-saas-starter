from __future__ import annotations

from collections.abc import Mapping
from typing import cast

import httpx
import pytest

from app.domain.secrets import SecretPurpose
from app.infrastructure.secrets.infisical_client import InfisicalAPIClient
from app.infrastructure.secrets.infisical_provider import InfisicalSecretProvider


class _MockTransport(httpx.BaseTransport):
    def __init__(self, responses: Mapping[str, tuple[int, dict[str, object]]]) -> None:
        self.responses = responses

    def handle_request(self, request: httpx.Request) -> httpx.Response:  # type: ignore[override]
        key = f"{request.method} {request.url.path}"
        status, payload = self.responses.get(
            key,
            (404, {"message": "not found"}),
        )
        return httpx.Response(status, request=request, json=payload)


@pytest.mark.asyncio
async def test_sign_and_verify_hmac_caching() -> None:
    responses: dict[str, tuple[int, dict[str, object]]] = {
        "GET /api/v4/secrets/auth-service-signing-secret": (
            200,
            cast(dict[str, object], {"secret": {"secretValue": "super-secret"}}),
        ),
    }
    client = InfisicalAPIClient(
        base_url="https://infisical.local",
        service_token="st.test",
        project_id="proj",
        environment="dev",
        secret_path="/backend",
        transport=_MockTransport(responses),
    )
    provider = InfisicalSecretProvider(
        client=client,
        signing_secret_name="auth-service-signing-secret",
        cache_ttl_seconds=60,
    )
    payload = b'{"account":"ci"}'
    signed = await provider.sign(payload, purpose=SecretPurpose.SERVICE_ACCOUNT_ISSUANCE)
    assert signed.algorithm == "infisical-hmac-sha256"
    assert await provider.verify(
        payload,
        signed.signature,
        purpose=SecretPurpose.SERVICE_ACCOUNT_ISSUANCE,
    )
