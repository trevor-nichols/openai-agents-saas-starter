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

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=self._status_code,
            content=json.dumps(self._payload),
            request=request,
        )


class HeaderCaptureTransport(httpx.BaseTransport):
    def __init__(self, expected_namespace: str):
        self.expected_namespace = expected_namespace
        self.last_request: httpx.Request | None = None

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.last_request = request
        return httpx.Response(status_code=500, json={"errors": ["forced"]}, request=request)


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


def test_vault_namespace_header(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = HeaderCaptureTransport(expected_namespace="admin/tenant")
    client = VaultTransitClient(
        base_url="https://vault",
        token="token",
        key_name="auth-service",
        namespace="admin/tenant",
    )

    with pytest.raises(VaultVerificationError):
        client.verify_signature("payload", "signature", transport=transport)

    assert transport.last_request is not None
    headers = transport.last_request.headers
    assert headers.get("X-Vault-Namespace") == "admin/tenant"
