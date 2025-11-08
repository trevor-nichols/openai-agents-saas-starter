"""Unit tests for EdDSA signer, verifier, and auth dependencies."""

from __future__ import annotations

import base64
import json
import time

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.keys import load_keyset
from app.core.security import (
    TokenVerifierError,
    get_current_user,
    get_token_signer,
    get_token_verifier,
)


def _payload(
    *,
    iat_offset: int = 0,
    exp_offset: int = 300,
    token_use: str = "access",
    subject: str = "user:123",
) -> dict[str, int | str]:
    now = int(time.time()) + iat_offset
    return {
        "sub": subject,
        "scope": "conversations:read",
        "token_use": token_use,
        "iat": now,
        "nbf": now,
        "exp": now + exp_offset,
    }


def test_sign_and_verify_round_trip() -> None:
    signer = get_token_signer()
    verifier = get_token_verifier()

    signed = signer.sign(_payload())

    assert signed.primary.kid == "ed25519-active-test"
    claims = verifier.verify(signed.primary.token)
    assert claims["sub"] == "user:123"
    assert claims["scope"] == "conversations:read"


def test_verifier_rejects_tampered_payload() -> None:
    signer = get_token_signer()
    verifier = get_token_verifier()

    signed = signer.sign(_payload())
    header, payload, signature = signed.primary.token.split(".")
    padding = "=" * ((4 - len(payload) % 4) % 4)
    payload_bytes = base64.urlsafe_b64decode(f"{payload}{padding}")
    tampered = json.loads(payload_bytes)
    tampered["scope"] = "tampered"
    new_payload = (
        base64.urlsafe_b64encode(json.dumps(tampered).encode("utf-8")).decode("utf-8").rstrip("=")
    )
    tampered_token = ".".join([header, new_payload, signature])

    with pytest.raises(TokenVerifierError):
        verifier.verify(tampered_token)


def test_verifier_rejects_unknown_kid() -> None:
    signer = get_token_signer()
    verifier = get_token_verifier()
    signed = signer.sign(_payload())
    header, payload, signature = signed.primary.token.split(".")
    header_padding = "=" * ((4 - len(header) % 4) % 4)
    header_bytes = base64.urlsafe_b64decode(f"{header}{header_padding}")
    new_header = json.loads(header_bytes)
    new_header["kid"] = "ed25519-missing"
    encoded = (
        base64.urlsafe_b64encode(json.dumps(new_header).encode("utf-8")).decode("utf-8").rstrip("=")
    )
    swapped = ".".join([encoded, payload, signature])

    with pytest.raises(TokenVerifierError):
        verifier.verify(swapped)


def test_verifier_rejects_expired_token() -> None:
    signer = get_token_signer()
    verifier = get_token_verifier()
    signed = signer.sign(_payload(iat_offset=-600, exp_offset=-60))

    with pytest.raises(TokenVerifierError):
        verifier.verify(signed.primary.token)


def test_verifier_rejects_token_signed_with_next_key() -> None:
    keyset = load_keyset()
    next_material = getattr(keyset, "next", None)
    if not next_material or not next_material.private_key:
        pytest.skip("Test keyset does not define a next key with private material.")

    headers = {"kid": next_material.kid, "alg": "EdDSA", "typ": "JWT"}
    token = jwt.encode(_payload(), next_material.private_key, algorithm="EdDSA", headers=headers)
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    verifier = get_token_verifier()

    with pytest.raises(TokenVerifierError):
        verifier.verify(token)


@pytest.mark.asyncio
async def test_get_current_user_accepts_access_token() -> None:
    signer = get_token_signer()
    token = signer.sign(_payload()).primary.token
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    user = await get_current_user(credentials)

    assert user["user_id"] == "123"
    assert user["payload"]["token_use"] == "access"


@pytest.mark.asyncio
async def test_get_current_user_rejects_refresh_token() -> None:
    signer = get_token_signer()
    token = signer.sign(_payload(token_use="refresh")).primary.token
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_rejects_non_user_subject() -> None:
    signer = get_token_signer()
    bundle = signer.sign(_payload(subject="service-account:analytics"))
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=bundle.primary.token)

    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials)

    assert exc.value.detail == "Token subject must reference a user account."
