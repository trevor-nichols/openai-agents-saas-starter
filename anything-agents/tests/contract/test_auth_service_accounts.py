"""Contract tests covering service-account issuance via CLI."""

from __future__ import annotations

import time
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.cli.auth_cli import build_parser, handle_issue_service_account
from app.infrastructure.security.nonce_store import InMemoryNonceStore
from app.core import config as config_module
from app.core.security import get_token_verifier
from main import app


class FakeVaultClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def verify_signature(self, payload_b64: str, signature: str) -> bool:
        self.calls.append((payload_b64, signature))
        return True


def test_cli_roundtrip_enforces_nonce_reuse(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # Route CLI HTTP calls through the FastAPI app.
    test_client = TestClient(app)

    class DummyHttpxClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401 - signature shaped like httpx.Client
            self._client = test_client

        def __enter__(self) -> DummyHttpxClient:
            return self

        def __exit__(self, *_: Any) -> None:
            return None

        def post(self, url: str, json: dict[str, Any], headers: dict[str, str]) -> Any:
            response = self._client.post(url, json=json, headers=headers)

            class _Wrapper:
                def __init__(self, res) -> None:
                    self._res = res
                    self.status_code = res.status_code
                    self.text = res.text

                def json(self) -> Any:
                    return self._res.json()

            return _Wrapper(response)

    monkeypatch.setattr("app.cli.auth_cli.httpx.Client", DummyHttpxClient)

    monkeypatch.setenv("VAULT_VERIFY_ENABLED", "true")
    monkeypatch.setenv("VAULT_ADDR", "https://vault.local")
    monkeypatch.setenv("VAULT_TOKEN", "test-token")
    config_module.get_settings.cache_clear()

    fake_client = FakeVaultClient()
    nonce_store = InMemoryNonceStore()
    monkeypatch.setattr("app.api.v1.auth.router.get_vault_transit_client", lambda: fake_client)
    monkeypatch.setattr("app.api.v1.auth.router.get_nonce_store", lambda: nonce_store)

    issued_at = int(time.time())

    def fake_envelope(request_payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "iss": "vault-transit",
            "aud": ["auth-service"],
            "sub": "service-account-cli",
            "account": request_payload.get("account"),
            "tenant_id": request_payload.get("tenant_id"),
            "scopes": request_payload.get("scopes", []),
            "nonce": "fixed-nonce",
            "iat": issued_at,
            "exp": issued_at + 300,
        }

    signed_payloads: list[str] = []

    def fake_sign(*, payload_b64: str, **_: Any) -> str:
        signed_payloads.append(payload_b64)
        return "signature"

    monkeypatch.setattr("app.cli.auth_cli._build_vault_envelope", fake_envelope)
    monkeypatch.setattr("app.cli.auth_cli._vault_sign_payload", fake_sign)

    parser = build_parser()
    args = parser.parse_args(
        [
            "tokens",
            "issue-service-account",
            "--account",
            "analytics-batch",
            "--scopes",
            "conversations:read",
            "--tenant",
            "11111111-2222-3333-4444-555555555555",
            "--base-url",
            "http://testserver",
        ]
    )

    first_exit = handle_issue_service_account(args)
    first_output = capsys.readouterr()

    assert first_exit == 0
    assert '"refresh_token"' in first_output.out
    assert fake_client.calls, "Vault verification was not invoked."
    assert len(signed_payloads) == 1

    second_exit = handle_issue_service_account(args)
    second_output = capsys.readouterr()

    assert second_exit == 1
    assert "error: Issuance failed (401): Vault payload nonce already used." in second_output.err
    assert len(signed_payloads) == 2
    assert signed_payloads[0] == signed_payloads[1]

    config_module.get_settings.cache_clear()
    test_client.close()


def test_service_account_issue_returns_eddsa_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VAULT_VERIFY_ENABLED", "false")
    config_module.get_settings.cache_clear()
    client = TestClient(app)

    payload = {
        "account": "analytics-batch",
        "scopes": ["conversations:read"],
        "tenant_id": "11111111-2222-3333-4444-555555555555",
        "lifetime_minutes": 30,
        "fingerprint": "contract-test",
        "force": True,
    }
    response = client.post(
        "/api/v1/auth/service-accounts/issue",
        json=payload,
        headers={"Authorization": "Bearer dev-local"},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    verifier = get_token_verifier()
    claims = verifier.verify(body["refresh_token"])

    assert body["kid"] == "ed25519-active-test"
    assert claims["token_use"] == "refresh"
    assert claims["account"] == "analytics-batch"
    assert claims["tenant_id"] == payload["tenant_id"]

    client.close()
    config_module.get_settings.cache_clear()
