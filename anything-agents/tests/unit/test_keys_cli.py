"""Unit tests for key rotation CLI."""

from __future__ import annotations

import json
import time

from app.cli.auth_cli import build_parser, handle_keys_rotate
from app.core import config as config_module
from app.core.keys import FileKeyStorage
from app.core.security import get_token_signer, get_token_verifier


def test_keys_rotate_command(tmp_path, monkeypatch, capsys) -> None:
    storage_path = tmp_path / "keys.json"
    monkeypatch.setenv("AUTH_KEY_STORAGE_BACKEND", "file")
    monkeypatch.setenv("AUTH_KEY_STORAGE_PATH", str(storage_path))

    config_module.get_settings.cache_clear()

    parser = build_parser()
    args = parser.parse_args(["keys", "rotate", "--kid", "test-kid"])

    exit_code = handle_keys_rotate(args)
    output = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(output.out)
    assert payload["kid"] == "test-kid"
    assert payload["status"] == "active"

    # Rotate again to ensure "next" assignment works.
    args_second = parser.parse_args(["keys", "rotate"])
    exit_code_second = handle_keys_rotate(args_second)
    assert exit_code_second == 0

    storage = FileKeyStorage(storage_path)
    keyset = storage.load_keyset()
    assert keyset.active
    assert keyset.next

    config_module.get_settings.cache_clear()


def test_key_rotation_smoke_sign_and_verify(tmp_path, monkeypatch) -> None:
    """Ensure rotated keys can immediately issue and verify JWTs."""

    storage_path = tmp_path / "keys.json"
    monkeypatch.setenv("AUTH_KEY_STORAGE_BACKEND", "file")
    monkeypatch.setenv("AUTH_KEY_STORAGE_PATH", str(storage_path))
    config_module.get_settings.cache_clear()

    parser = build_parser()
    args = parser.parse_args(["keys", "rotate", "--activate-now"])
    assert handle_keys_rotate(args) == 0

    settings = config_module.get_settings()
    signer = get_token_signer(settings)
    verifier = get_token_verifier(settings)

    now = int(time.time())
    payload = {
        "sub": "user:rotation-smoke",
        "scope": "conversations:read",
        "token_use": "access",
        "iat": now,
        "nbf": now,
        "exp": now + 300,
    }

    signed = signer.sign(payload)
    claims = verifier.verify(signed.primary.token)

    assert claims["sub"] == "user:rotation-smoke"
    assert signed.primary.kid != "ed25519-active-test"

    config_module.get_settings.cache_clear()
