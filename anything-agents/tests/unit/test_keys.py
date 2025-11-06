"""Unit tests for key lifecycle helpers."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from app.core.keys import (
    FileKeyStorage,
    KeyRotationError,
    KeySet,
    KeyStatus,
    KeyStorageError,
    SecretManagerKeyStorage,
    generate_ed25519_keypair,
    register_secret_manager_client,
    reset_secret_manager_client,
)


def test_keyset_insert_promotes_initial_key() -> None:
    keyset = KeySet.empty()
    key = generate_ed25519_keypair(status=KeyStatus.ACTIVE)

    keyset.insert(key)

    assert keyset.active and keyset.active.kid == key.kid
    assert keyset.next is None


def test_keyset_insert_next_moves_previous_to_retired() -> None:
    keyset = KeySet.empty()
    active = generate_ed25519_keypair(status=KeyStatus.ACTIVE)
    first_next = generate_ed25519_keypair(status=KeyStatus.NEXT)
    keyset.insert(active)
    keyset.insert(first_next)

    replacement = generate_ed25519_keypair(status=KeyStatus.NEXT)
    keyset.insert(replacement)

    assert keyset.next and keyset.next.kid == replacement.kid
    assert any(entry.kid == first_next.kid for entry in keyset.retired)


def test_keyset_overlap_validation(tmp_path) -> None:
    keyset = KeySet.empty()
    old_active = generate_ed25519_keypair(status=KeyStatus.ACTIVE)
    keyset.insert(old_active)

    far_future = generate_ed25519_keypair(status=KeyStatus.NEXT)
    future_ts = old_active.created_at + timedelta(days=7)
    far_future = replace(
        far_future,
        created_at=future_ts,
        not_before=future_ts,
    )
    keyset.insert(far_future)

    with pytest.raises(KeyRotationError):
        keyset.ensure_overlap_within(max_minutes=60)


def test_file_key_storage_roundtrip(tmp_path) -> None:
    storage = FileKeyStorage(tmp_path / "keys.json")
    keyset = KeySet.empty()
    keyset.insert(generate_ed25519_keypair(status=KeyStatus.ACTIVE))
    keyset.insert(generate_ed25519_keypair(status=KeyStatus.NEXT))

    storage.save_keyset(keyset)
    loaded = storage.load_keyset()

    assert loaded.active and keyset.active
    assert loaded.active.kid == keyset.active.kid
    assert loaded.next and keyset.next
    assert loaded.next.kid == keyset.next.kid


class InMemorySecretManagerClient:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def read_secret(self, name: str) -> str | None:
        return self.store.get(name)

    def write_secret(self, name: str, value: str) -> None:
        self.store[name] = value


def test_secret_manager_storage_roundtrip() -> None:
    client = InMemorySecretManagerClient()
    register_secret_manager_client(lambda: client)
    storage = SecretManagerKeyStorage("auth/keyset")

    keyset = KeySet.empty()
    keyset.insert(generate_ed25519_keypair(status=KeyStatus.ACTIVE))
    storage.save_keyset(keyset)

    loaded = storage.load_keyset()
    assert loaded.active
    assert loaded.active.kid == keyset.active.kid

    reset_secret_manager_client()


def test_materialize_jwks_caches_until_fingerprint_changes() -> None:
    keyset = KeySet.empty()
    active = generate_ed25519_keypair(status=KeyStatus.ACTIVE)
    keyset.insert(active)

    first = keyset.materialize_jwks()
    second = keyset.materialize_jwks()
    assert first is second

    nxt = generate_ed25519_keypair(status=KeyStatus.NEXT)
    keyset.insert(nxt)

    refreshed = keyset.materialize_jwks()
    assert refreshed is not first
    assert {entry["kid"] for entry in refreshed.payload["keys"]} == {active.kid, nxt.kid}


def test_materialize_jwks_excludes_retired_keys() -> None:
    keyset = KeySet.empty()
    first_active = generate_ed25519_keypair(status=KeyStatus.ACTIVE)
    keyset.insert(first_active)
    first_next = generate_ed25519_keypair(status=KeyStatus.NEXT)
    keyset.insert(first_next)

    new_active = generate_ed25519_keypair(status=KeyStatus.ACTIVE)
    keyset.insert(new_active)
    new_next = generate_ed25519_keypair(status=KeyStatus.NEXT)
    keyset.insert(new_next)

    doc = keyset.materialize_jwks()
    kids = {entry["kid"] for entry in doc.payload["keys"]}

    assert new_active.kid in kids
    assert new_next.kid in kids
    assert first_active.kid not in kids
    assert first_next.kid not in kids
