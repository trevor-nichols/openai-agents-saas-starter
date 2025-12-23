"""Key rotation service for CLI-facing workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from starter_contracts.keys import (
    KeyStorageError,
    generate_ed25519_keypair,
    load_keyset,
    save_keyset,
)

from starter_cli.core import CLIContext, CLIError

from .key_storage import configure_key_storage_secret_manager


@dataclass(frozen=True, slots=True)
class KeyRotationResult:
    kid: str
    public_jwk: dict[str, Any]
    storage_backend: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "kid": self.kid,
            "public_jwk": self.public_jwk,
            "storage_backend": self.storage_backend,
        }


def rotate_signing_keys(ctx: CLIContext, *, kid: str | None) -> KeyRotationResult:
    settings = ctx.require_settings()
    configure_key_storage_secret_manager(ctx)

    try:
        keyset = load_keyset(settings)
    except KeyStorageError as exc:  # pragma: no cover - depends on env
        raise CLIError(str(exc)) from exc

    try:
        material = generate_ed25519_keypair(kid=kid)
        keyset.set_active(material)
        save_keyset(keyset, settings)
    except KeyStorageError as exc:  # pragma: no cover - depends on env
        raise CLIError(str(exc)) from exc

    return KeyRotationResult(
        kid=material.kid,
        public_jwk=material.public_jwk,
        storage_backend=settings.auth_key_storage_backend,
    )


__all__ = ["KeyRotationResult", "rotate_signing_keys"]
