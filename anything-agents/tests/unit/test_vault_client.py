"""Unit tests for Vault Transit client."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from app.infrastructure.security.vault import VaultTransitClient, VaultVerificationError


class MockTransport(httpx.BaseTransport):
    def __init__(self, status_code: int, payload: dict[str, Any]):
        self._status_code = status_code
        self._payload = payload

    def handle_request(self, request: httpx.Request) -> httpx.Response:  # type: ignore[override]
        return httpx.Response(
            status_code=self._status_code,
            content=json.dumps(self._payload),
            request=request,
        )


def test_vault_verify_success(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = MockTransport(200, {"data": {"valid": True}})

    client = VaultTransitClient(base_url="https://vault", token="token", key_name="auth-service")
    assert client.verify_signature("payload", "signature", transport=transport) is True


def test_vault_verify_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = MockTransport(200, {"data": {"valid": False}})

    client = VaultTransitClient(base_url="https://vault", token="token", key_name="auth-service")
    assert client.verify_signature("payload", "signature", transport=transport) is False


def test_vault_verify_error(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = MockTransport(500, {"errors": ["failure"]})

    client = VaultTransitClient(base_url="https://vault", token="token", key_name="auth-service")

    with pytest.raises(VaultVerificationError):
        client.verify_signature("payload", "signature", transport=transport)
