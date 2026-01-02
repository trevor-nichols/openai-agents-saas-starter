from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.services.sso.oidc_client import OidcClient, OidcTokenVerificationError


def _build_rsa_jwk(kid: str) -> tuple[rsa.RSAPrivateKey, dict[str, object]]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(public_key))
    jwk["kid"] = kid
    return private_key, jwk


def _encode_token(
    private_key: rsa.RSAPrivateKey, *, kid: str, payload: dict[str, object]
) -> str:
    token = jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": kid})
    if isinstance(token, bytes):
        return token.decode("utf-8")
    return token


@pytest.mark.asyncio
async def test_verify_id_token_requires_exp(monkeypatch: pytest.MonkeyPatch) -> None:
    private_key, jwk = _build_rsa_jwk("kid-exp")
    now = datetime.now(UTC)
    token = _encode_token(
        private_key,
        kid="kid-exp",
        payload={
            "sub": "subject",
            "iss": "https://issuer.example.com",
            "aud": "client-id",
            "iat": int(now.timestamp()),
        },
    )

    client = OidcClient()

    async def _fake_fetch(_jwks_uri: str):
        return {"keys": [jwk]}

    monkeypatch.setattr(client, "_fetch_jwks", _fake_fetch)

    with pytest.raises(OidcTokenVerificationError):
        await client.verify_id_token(
            id_token=token,
            issuer="https://issuer.example.com",
            audience="client-id",
            jwks_uri="https://issuer.example.com/jwks",
            allowed_algs=["RS256"],
        )

    await client.close()


@pytest.mark.asyncio
async def test_verify_id_token_requires_iat(monkeypatch: pytest.MonkeyPatch) -> None:
    private_key, jwk = _build_rsa_jwk("kid-iat")
    now = datetime.now(UTC)
    token = _encode_token(
        private_key,
        kid="kid-iat",
        payload={
            "sub": "subject",
            "iss": "https://issuer.example.com",
            "aud": "client-id",
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        },
    )

    client = OidcClient()

    async def _fake_fetch(_jwks_uri: str):
        return {"keys": [jwk]}

    monkeypatch.setattr(client, "_fetch_jwks", _fake_fetch)

    with pytest.raises(OidcTokenVerificationError):
        await client.verify_id_token(
            id_token=token,
            issuer="https://issuer.example.com",
            audience="client-id",
            jwks_uri="https://issuer.example.com/jwks",
            allowed_algs=["RS256"],
        )

    await client.close()


@pytest.mark.asyncio
async def test_exchange_code_omits_client_id_for_basic_auth() -> None:
    captured: dict[str, str | None] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = (await request.aread()).decode()
        captured["authorization"] = request.headers.get("authorization")
        return httpx.Response(200, json={"id_token": "token"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = OidcClient(http_client)
        await client.exchange_code_for_tokens(
            token_endpoint="https://issuer.example.com/token",
            client_id="client-id",
            client_secret="secret",
            code="code",
            redirect_uri="https://app.example.com/callback",
            code_verifier=None,
            token_auth_method="client_secret_basic",
        )

    body = parse_qs(captured.get("body") or "")
    assert "client_id" not in body
    assert captured.get("authorization")


@pytest.mark.asyncio
async def test_exchange_code_includes_client_id_for_post_auth() -> None:
    captured: dict[str, str | None] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = (await request.aread()).decode()
        return httpx.Response(200, json={"id_token": "token"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = OidcClient(http_client)
        await client.exchange_code_for_tokens(
            token_endpoint="https://issuer.example.com/token",
            client_id="client-id",
            client_secret="secret",
            code="code",
            redirect_uri="https://app.example.com/callback",
            code_verifier=None,
            token_auth_method="client_secret_post",
        )

    body = parse_qs(captured.get("body") or "")
    assert body.get("client_id") == ["client-id"]
    assert body.get("client_secret") == ["secret"]
