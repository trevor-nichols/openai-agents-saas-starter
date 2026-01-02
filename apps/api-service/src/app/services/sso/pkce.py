"""PKCE and state helpers for SSO flows."""

from __future__ import annotations

import base64
import hashlib
import secrets


def generate_state() -> str:
    return secrets.token_urlsafe(32)


def generate_nonce() -> str:
    return secrets.token_urlsafe(24)


def generate_pkce_verifier() -> str:
    raw = secrets.token_bytes(32)
    return _urlsafe_b64(raw)


def code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return _urlsafe_b64(digest)


def _urlsafe_b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


__all__ = [
    "code_challenge",
    "generate_nonce",
    "generate_pkce_verifier",
    "generate_state",
]
