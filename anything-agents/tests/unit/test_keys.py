"""Unit tests for simplified key storage helpers."""

from __future__ import annotations

from datetime import datetime

from app.core.keys import (
    FileKeyStorage,
    KeyMaterial,
    KeySet,
    SecretManagerKeyStorage,
    generate_ed25519_keypair,
    register_secret_manager_client,
    reset_secret_manager_client,
)


def test_set_active_overwrites_previous() -> None:
    keyset = KeySet.empty()
    first = generate_ed25519_keypair(kid="first")
    second = generate_ed25519_keypair(kid="second")

    keyset.set_active(first)
    assert keyset.active and keyset.active.kid == "first"

    keyset.set_active(second)
    assert keyset.active and keyset.active.kid == "second"


def test_file_key_storage_roundtrip(tmp_path) -> None:
    storage = FileKeyStorage(tmp_path / "keys.json")
    keyset = KeySet.empty()
    keyset.set_active(generate_ed25519_keypair(kid="file-test"))

    storage.save_keyset(keyset)
    loaded = storage.load_keyset()

    assert loaded.active
    assert loaded.active.kid == "file-test"


class FakeSecretClient:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def read_secret(self, name: str) -> str | None:
        return self.store.get(name)

    def write_secret(self, name: str, value: str) -> None:
        self.store[name] = value


def test_secret_manager_storage_roundtrip() -> None:
    client = FakeSecretClient()
    register_secret_manager_client(lambda: client)

    storage = SecretManagerKeyStorage("auth/keyset")
    keyset = KeySet.empty()
    keyset.set_active(generate_ed25519_keypair(kid="vault-test"))
    storage.save_keyset(keyset)

    loaded = storage.load_keyset()
    assert loaded.active and loaded.active.kid == "vault-test"

    reset_secret_manager_client()


def test_materialize_jwks_single_key() -> None:
    keyset = KeySet.empty()
    material = generate_ed25519_keypair(kid="jwks-test")
    keyset.set_active(material)

    doc = keyset.materialize_jwks()
    assert doc.payload["keys"][0]["kid"] == "jwks-test"

    # Cached instance reused when nothing changes.
    doc_again = keyset.materialize_jwks()
    assert doc_again is doc

    # Mutating the active key busts the cache.
    replacement = KeyMaterial(
        kid="jwks-new",
        private_key=material.private_key,
        public_jwk=material.public_jwk,
        created_at=datetime.now(material.created_at.tzinfo),
        not_before=material.not_before,
        not_after=None,
    )
    keyset.set_active(replacement)
    assert keyset.materialize_jwks() is not doc
