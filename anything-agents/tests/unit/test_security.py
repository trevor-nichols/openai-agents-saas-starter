"""Unit tests for EdDSA signer and verifier helpers."""

from __future__ import annotations

import base64
import json
import time

import pytest

from app.core.security import (
    TokenVerifierError,
    get_token_signer,
    get_token_verifier,
)


def _payload(iat_offset: int = 0, exp_offset: int = 300) -> dict[str, int | str]:
    now = int(time.time()) + iat_offset
    return {
        "sub": "user-123",
        "scope": "conversations:read",
        "token_use": "access",
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
    assert claims["sub"] == "user-123"
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
    new_payload = base64.urlsafe_b64encode(json.dumps(tampered).encode("utf-8")).decode("utf-8").rstrip("=")
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
    encoded = base64.urlsafe_b64encode(json.dumps(new_header).encode("utf-8")).decode("utf-8").rstrip("=")
    swapped = ".".join([encoded, payload, signature])

    with pytest.raises(TokenVerifierError):
        verifier.verify(swapped)


def test_verifier_rejects_expired_token() -> None:
    signer = get_token_signer()
    verifier = get_token_verifier()
    signed = signer.sign(_payload(iat_offset=-600, exp_offset=-60))

    with pytest.raises(TokenVerifierError):
        verifier.verify(signed.primary.token)
