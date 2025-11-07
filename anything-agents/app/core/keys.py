"""Minimal Ed25519 key storage helpers for the auth stack."""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol
from uuid import uuid4

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from app.core.config import Settings, get_settings

UTC = timezone.utc
KEYSET_SCHEMA_VERSION = 1


class KeySetError(RuntimeError):
    """Base class for key lifecycle failures."""


class KeyStorageError(KeySetError):
    """Raised when keys cannot be read/written from the configured backend."""


@dataclass(frozen=True)
class KeyMaterial:
    """Serialized Ed25519 keypair metadata."""

    kid: str
    private_key: str | None
    public_jwk: dict[str, Any]
    created_at: datetime
    not_before: datetime
    not_after: datetime | None = None

    def to_dict(self, *, include_private: bool = True) -> dict[str, Any]:
        payload = {
            "kid": self.kid,
            "public_jwk": self.public_jwk,
            "created_at": self.created_at.isoformat(),
            "not_before": self.not_before.isoformat(),
            "not_after": self.not_after.isoformat() if self.not_after else None,
        }
        if include_private:
            payload["private_key"] = self.private_key
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KeyMaterial":
        return cls(
            kid=data["kid"],
            private_key=data.get("private_key"),
            public_jwk=data["public_jwk"],
            created_at=datetime.fromisoformat(data["created_at"]),
            not_before=datetime.fromisoformat(data["not_before"]),
            not_after=datetime.fromisoformat(data["not_after"]) if data.get("not_after") else None,
        )


@dataclass(frozen=True)
class JWKSDocument:
    payload: dict[str, Any]
    fingerprint: str
    last_modified: datetime


class KeySet:
    """Container that holds a single active Ed25519 key."""

    def __init__(self, *, active: KeyMaterial | None) -> None:
        self.active = active
        self._cached_jwks: JWKSDocument | None = None

    @classmethod
    def empty(cls) -> "KeySet":
        return cls(active=None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": KEYSET_SCHEMA_VERSION,
            "active": self.active.to_dict() if self.active else None,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "KeySet":
        active = KeyMaterial.from_dict(payload["active"]) if payload.get("active") else None
        return cls(active=active)

    def set_active(self, material: KeyMaterial) -> None:
        """Replace the active key with new material."""

        self.active = material
        self._cached_jwks = None

    def materialize_jwks(self) -> JWKSDocument:
        fingerprint = self._jwks_fingerprint()
        if self._cached_jwks and self._cached_jwks.fingerprint == fingerprint:
            return self._cached_jwks

        if not self.active or not self.active.public_jwk:
            keys: list[dict[str, Any]] = []
            last_modified = datetime.now(UTC)
        else:
            keys = [json.loads(json.dumps(self.active.public_jwk))]
            last_modified = self.active.created_at

        doc = JWKSDocument(payload={"keys": keys}, fingerprint=fingerprint, last_modified=last_modified)
        self._cached_jwks = doc
        return doc

    def to_jwks(self) -> dict[str, Any]:
        return json.loads(json.dumps(self.materialize_jwks().payload))

    def _jwks_fingerprint(self) -> str:
        if not self.active or not self.active.public_jwk:
            return "empty"
        parts = [
            str(KEYSET_SCHEMA_VERSION),
            self.active.kid,
            json.dumps(self.active.public_jwk, sort_keys=True),
            self.active.created_at.isoformat(),
        ]
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


class KeyStorageAdapter(Protocol):
    def load_keyset(self) -> KeySet:
        ...

    def save_keyset(self, keyset: KeySet) -> None:
        ...


class FileKeyStorage(KeyStorageAdapter):
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load_keyset(self) -> KeySet:
        if not self.path.exists():
            return KeySet.empty()
        try:
            data = json.loads(self.path.read_text())
        except Exception as exc:  # noqa: BLE001
            raise KeyStorageError(f"Failed to read keyset file: {exc}") from exc
        return KeySet.from_dict(data)

    def save_keyset(self, keyset: KeySet) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(keyset.to_dict(), indent=2))
        except Exception as exc:  # noqa: BLE001
            raise KeyStorageError(f"Failed to write keyset file: {exc}") from exc


class SecretManagerClient(Protocol):
    def read_secret(self, name: str) -> str | None:
        ...

    def write_secret(self, name: str, value: str) -> None:
        ...


_secret_manager_client_factory: Callable[[], SecretManagerClient] | None = None


def register_secret_manager_client(factory: Callable[[], SecretManagerClient]) -> None:
    global _secret_manager_client_factory
    _secret_manager_client_factory = factory


def reset_secret_manager_client() -> None:
    global _secret_manager_client_factory
    _secret_manager_client_factory = None


def _get_secret_manager_client() -> SecretManagerClient:
    if _secret_manager_client_factory is None:
        raise KeyStorageError("Secret manager client is not configured.")
    return _secret_manager_client_factory()


class SecretManagerKeyStorage(KeyStorageAdapter):
    def __init__(self, secret_name: str) -> None:
        self.secret_name = secret_name

    def load_keyset(self) -> KeySet:
        client = _get_secret_manager_client()
        raw = client.read_secret(self.secret_name)
        if not raw:
            return KeySet.empty()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise KeyStorageError(f"Secret manager payload invalid JSON: {exc}") from exc
        return KeySet.from_dict(payload)

    def save_keyset(self, keyset: KeySet) -> None:
        client = _get_secret_manager_client()
        client.write_secret(self.secret_name, json.dumps(keyset.to_dict()))


def get_key_storage(settings: Settings | None = None) -> KeyStorageAdapter:
    settings = settings or get_settings()
    backend = settings.auth_key_storage_backend
    if backend == "file":
        return FileKeyStorage(settings.auth_key_storage_path)
    if backend == "secret-manager":
        if not settings.auth_key_secret_name:
            raise KeyStorageError("auth_key_secret_name must be set for secret-manager backend.")
        return SecretManagerKeyStorage(settings.auth_key_secret_name)
    raise KeyStorageError(f"Unsupported key storage backend: {backend}")


def load_keyset(settings: Settings | None = None) -> KeySet:
    storage = get_key_storage(settings)
    return storage.load_keyset()


def save_keyset(keyset: KeySet, settings: Settings | None = None) -> None:
    storage = get_key_storage(settings)
    storage.save_keyset(keyset)


def generate_ed25519_keypair(*, kid: str | None = None) -> KeyMaterial:
    kid = kid or f"ed25519-{uuid4().hex[:12]}"
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    public_b64 = base64.urlsafe_b64encode(public_bytes).decode("utf-8").rstrip("=")

    jwk = {
        "kty": "OKP",
        "crv": "Ed25519",
        "kid": kid,
        "x": public_b64,
        "use": "sig",
        "alg": "EdDSA",
    }

    created = datetime.now(UTC)
    return KeyMaterial(
        kid=kid,
        private_key=private_pem,
        public_jwk=jwk,
        created_at=created,
        not_before=created,
        not_after=None,
    )


__all__ = [
    "KeyMaterial",
    "KeySet",
    "KeySetError",
    "KeyStorageError",
    "FileKeyStorage",
    "SecretManagerKeyStorage",
    "generate_ed25519_keypair",
    "load_keyset",
    "save_keyset",
    "register_secret_manager_client",
    "reset_secret_manager_client",
]
