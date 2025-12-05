"""Tests for the Vault KV secret manager adapter."""

from __future__ import annotations

import json
from collections.abc import Callable

import httpx
import pytest
from starter_contracts import vault_kv as shared_vault_kv

from app.core import settings as config_module
from app.infrastructure.security import vault_kv
from app.infrastructure.security.vault_kv import VaultKVSecretManagerClient


def test_vault_kv_client_read_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Vault-Token"] == "token"
        return httpx.Response(
            200,
            json={"data": {"data": {"value": '{"schema_version":1}'}}},
            request=request,
        )

    transport = httpx.MockTransport(handler)
    client = VaultKVSecretManagerClient(
        base_url="https://vault.local",
        token="token",
        transport=transport,
    )

    value = client.read_secret("kv/data/auth/keyset")
    assert value == '{"schema_version":1}'


def test_vault_kv_client_write_success() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.content.decode()
        return httpx.Response(204, request=request)

    transport = httpx.MockTransport(handler)
    client = VaultKVSecretManagerClient(
        base_url="https://vault.local",
        token="token",
        transport=transport,
    )

    client.write_secret("kv/data/auth/keyset", '{"schema_version":1}')
    assert json.loads(captured["body"]) == {"data": {"value": '{"schema_version":1}'}}


def test_configure_vault_secret_manager_registers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_KEY_STORAGE_BACKEND", "secret-manager")
    monkeypatch.setenv("AUTH_KEY_SECRET_NAME", "kv/data/auth/keyset")
    monkeypatch.setenv("VAULT_ADDR", "https://vault.local")
    monkeypatch.setenv("VAULT_TOKEN", "token")
    config_module.get_settings.cache_clear()

    captured: dict[str, Callable[[], VaultKVSecretManagerClient]] = {}

    def fake_register(factory: Callable[[], VaultKVSecretManagerClient]) -> None:
        captured["factory"] = factory

    monkeypatch.setattr(
        shared_vault_kv,
        "register_secret_manager_client",
        fake_register,
    )

    vault_kv.configure_vault_secret_manager()

    assert "factory" in captured
    client = captured["factory"]()
    assert isinstance(client, VaultKVSecretManagerClient)

    config_module.get_settings.cache_clear()
