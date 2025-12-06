"""Backward-compatible shim for shared Vault KV helpers."""

from starter_contracts.vault_kv import (
    VaultKVSecretManagerClient,
    configure_vault_secret_manager,
)

__all__ = ["VaultKVSecretManagerClient", "configure_vault_secret_manager"]
