"""Backward-compatible shim that re-exports shared key helpers."""

from starter_contracts.keys import (
    FileKeyStorage,
    KeyMaterial,
    KeySet,
    KeySetError,
    KeyStorageError,
    SecretManagerKeyStorage,
    generate_ed25519_keypair,
    load_keyset,
    register_secret_manager_client,
    reset_secret_manager_client,
    save_keyset,
)

__all__ = [
    "FileKeyStorage",
    "KeyMaterial",
    "KeySet",
    "KeySetError",
    "KeyStorageError",
    "SecretManagerKeyStorage",
    "generate_ed25519_keypair",
    "load_keyset",
    "register_secret_manager_client",
    "reset_secret_manager_client",
    "save_keyset",
]
