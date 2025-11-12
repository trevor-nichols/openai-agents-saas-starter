"""Utilities for symmetric encryption of sensitive values."""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken


def build_cipher(secret: str | None) -> Fernet | None:
    """Build a deterministic Fernet cipher from an arbitrary secret."""

    if not secret:
        return None
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_optional(cipher: Fernet | None, value: str | None) -> bytes | None:
    if not cipher or not value:
        return None
    return cipher.encrypt(value.encode("utf-8"))


def decrypt_optional(cipher: Fernet | None, payload: bytes | None) -> str | None:
    if not cipher or not payload:
        return None
    try:
        return cipher.decrypt(payload).decode("utf-8")
    except InvalidToken:
        return None
