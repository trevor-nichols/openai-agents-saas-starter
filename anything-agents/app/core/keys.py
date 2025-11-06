"""Key lifecycle management helpers for Ed25519 signing keys."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Protocol
from uuid import uuid4

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from app.core.config import Settings, get_settings

UTC = timezone.utc
KEYSET_SCHEMA_VERSION = 1


class KeySetError(RuntimeError):
    """Base class for key lifecycle errors."""


class KeyRotationError(KeySetError):
    """Raised when rotation invariants are violated."""


class KeyStorageError(KeySetError):
    """Raised when key storage cannot be accessed."""


class KeyStatus(str, Enum):
    ACTIVE = "active"
    NEXT = "next"
    RETIRED = "retired"


@dataclass(frozen=True)
class KeyMaterial:
    """Represents a single Ed25519 keypair with metadata."""

    kid: str
    status: KeyStatus
    private_key: str | None
    public_jwk: dict[str, Any]
    created_at: datetime
    not_before: datetime
    not_after: datetime | None = None

    def to_dict(self, *, include_private: bool = True) -> dict[str, Any]:
        payload = {
            "kid": self.kid,
            "status": self.status.value,
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
            status=KeyStatus(data["status"]),
            private_key=data.get("private_key"),
            public_jwk=data["public_jwk"],
            created_at=datetime.fromisoformat(data["created_at"]),
            not_before=datetime.fromisoformat(data["not_before"]),
            not_after=datetime.fromisoformat(data["not_after"])
            if data.get("not_after")
            else None,
        )

    def as_status(self, status: KeyStatus) -> "KeyMaterial":
        return replace(self, status=status)


class KeySet:
    """Container tracking active/next/retired keys with rotation rules."""

    def __init__(
        self,
        *,
        active: KeyMaterial | None,
        next_key: KeyMaterial | None,
        retired: list[KeyMaterial] | None = None,
    ) -> None:
        self.active = active
        self.next = next_key
        self.retired = retired or []
        self._validate_uniqueness()

    @classmethod
    def empty(cls) -> "KeySet":
        return cls(active=None, next_key=None, retired=[])

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": KEYSET_SCHEMA_VERSION,
            "active": self.active.to_dict() if self.active else None,
            "next": self.next.to_dict() if self.next else None,
            "retired": [item.to_dict() for item in self.retired],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "KeySet":
        active = KeyMaterial.from_dict(payload["active"]) if payload.get("active") else None
        next_key = KeyMaterial.from_dict(payload["next"]) if payload.get("next") else None
        retired = [KeyMaterial.from_dict(item) for item in payload.get("retired", [])]
        return cls(active=active, next_key=next_key, retired=retired)

    def insert(self, material: KeyMaterial) -> None:
        if material.status == KeyStatus.ACTIVE:
            if self.active:
                self.retired.append(self.active.as_status(KeyStatus.RETIRED))
            self.active = material
        elif material.status == KeyStatus.NEXT:
            if self.next:
                self.retired.append(self.next.as_status(KeyStatus.RETIRED))
            self.next = material
        else:
            self.retired.append(material.as_status(KeyStatus.RETIRED))
        self._validate_uniqueness()

    def promote_next_to_active(self) -> None:
        if not self.next:
            raise KeyRotationError("No 'next' key available to promote.")
        promoted = self.next.as_status(KeyStatus.ACTIVE)
        if self.active:
            self.retired.append(self.active.as_status(KeyStatus.RETIRED))
        self.active = promoted
        self.next = None
        self._validate_uniqueness()

    def ensure_overlap_within(self, max_minutes: int) -> None:
        if not self.active or not self.next:
            return
        delta = (self.next.created_at - self.active.created_at).total_seconds() / 60
        if delta > max_minutes:
            raise KeyRotationError(
                f"Active/next key overlap window exceeded ({delta:.1f} min > {max_minutes} min)."
            )

    def to_jwks(self) -> dict[str, Any]:
        keys: list[dict[str, Any]] = []
        for material in [self.active, self.next]:
            if material and material.public_jwk:
                keys.append(material.public_jwk)
        return {"keys": keys}

    def _validate_uniqueness(self) -> None:
        seen: set[str] = set()
        for material in [self.active, self.next, *(self.retired or [])]:
            if not material:
                continue
            if material.kid in seen:
                raise KeyRotationError(f"Duplicate kid detected: {material.kid}")
            seen.add(material.kid)


class KeyStorageAdapter(Protocol):
    def load_keyset(self) -> KeySet:
        ...

    def save_keyset(self, keyset: KeySet) -> None:
        ...


class FileKeyStorage(KeyStorageAdapter):
    """Stores keyset data on the filesystem."""

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
    """Minimal secret-manager client interface."""

    def read_secret(self, name: str) -> str | None:
        ...

    def write_secret(self, name: str, value: str) -> None:
        ...


_secret_manager_client_factory: Callable[[], SecretManagerClient] | None = None


def register_secret_manager_client(factory: Callable[[], SecretManagerClient]) -> None:
    """Register a factory returning a concrete secret-manager client."""

    global _secret_manager_client_factory
    _secret_manager_client_factory = factory


def reset_secret_manager_client() -> None:
    """Reset the registered secret-manager client (useful for tests)."""

    global _secret_manager_client_factory
    _secret_manager_client_factory = None


def _get_secret_manager_client() -> SecretManagerClient:
    if _secret_manager_client_factory is None:
        raise KeyStorageError("Secret manager client is not configured.")
    return _secret_manager_client_factory()


class SecretManagerKeyStorage(KeyStorageAdapter):
    """Persists keyset JSON inside a secret-manager backend."""

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


def generate_ed25519_keypair(
    *,
    status: KeyStatus,
    kid: str | None = None,
    not_before: datetime | None = None,
) -> KeyMaterial:
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
    not_before = not_before or created

    return KeyMaterial(
        kid=kid,
        status=status,
        private_key=private_pem,
        public_jwk=jwk,
        created_at=created,
        not_before=not_before,
        not_after=None,
    )
