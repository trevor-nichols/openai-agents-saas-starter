"""Contract tests covering service-account issuance via the console."""

from __future__ import annotations

import base64
import json
import time
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fakeredis import FakeServer
from fakeredis.aioredis import FakeRedis
from fastapi.testclient import TestClient
from starter_console.commands.auth import build_parser, handle_issue_service_account

from app.core import settings as config_module
from app.core.keys import load_keyset
from app.core.security import get_token_signer, get_token_verifier
from app.domain.secrets import (
    SecretProviderHealth,
    SecretProviderStatus,
    SecretPurpose,
    SignedPayload,
)
from app.infrastructure.security.nonce_store import RedisNonceStore
from main import app


class FakeSecretProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[bytes, str, SecretPurpose]] = []

    async def get_secret(self, key: str, *, scope=None) -> str:  # pragma: no cover - unused
        raise NotImplementedError

    async def get_secrets(self, keys, *, scope=None) -> dict[str, str]:  # pragma: no cover - unused
        raise NotImplementedError

    async def sign(
        self, payload: bytes, *, purpose: SecretPurpose
    ) -> SignedPayload:  # pragma: no cover - unused
        raise NotImplementedError

    async def verify(
        self, payload: bytes, signature: str, *, purpose: SecretPurpose
    ) -> bool:
        self.calls.append((payload, signature, purpose))
        return True

    async def health_check(self) -> SecretProviderHealth:  # pragma: no cover - unused
        return SecretProviderHealth(status=SecretProviderStatus.HEALTHY, details={})


@pytest.fixture(autouse=True)
def stub_auth_service(monkeypatch: pytest.MonkeyPatch):
    signer = get_token_signer()
    keyset = load_keyset()
    active_kid = keyset.active.kid if keyset.active else "test-kid"

    class _StubAuthService:
        async def issue_service_account_refresh_token(
            self,
            *,
            account: str,
            scopes: list[str] | tuple[str, ...],
            tenant_id: str | None,
            requested_ttl_minutes: int | None,
            fingerprint: str | None,
            force: bool,
        ) -> dict[str, object | None]:
            issued_at = datetime.now(UTC)
            ttl = requested_ttl_minutes or 60
            expires_at = issued_at + timedelta(minutes=ttl)
            payload = {
                "sub": f"service-account:{account}",
                "token_use": "refresh",
                "account": account,
                "tenant_id": tenant_id,
                "scope": " ".join(scopes),
                "iat": int(issued_at.timestamp()),
                "exp": int(expires_at.timestamp()),
            }
            token = signer.sign(payload).primary.token
            return {
                "refresh_token": token,
                "expires_at": expires_at.isoformat(),
                "issued_at": issued_at.isoformat(),
                "scopes": list(scopes),
                "tenant_id": tenant_id,
                "kid": active_kid,
                "account": account,
                "token_use": "refresh",
                "session_id": None,
            }

    stub = _StubAuthService()
    monkeypatch.setattr("app.api.v1.auth.routes_service_accounts.auth_service", stub)
    return stub


def test_console_roundtrip_enforces_nonce_reuse(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Route console HTTP calls through the FastAPI app.
    with TestClient(app) as test_client:

        class DummyHttpxClient:
            def __init__(self, *args: Any, **kwargs: Any) -> None:
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

        monkeypatch.setattr("starter_console.services.auth.tokens.httpx.Client", DummyHttpxClient)

        monkeypatch.setenv("VAULT_VERIFY_ENABLED", "true")
        monkeypatch.setenv("VAULT_ADDR", "https://vault.local")
        monkeypatch.setenv("VAULT_TOKEN", "test-token")
        config_module.get_settings.cache_clear()

        fake_provider = FakeSecretProvider()
        fake_server = FakeServer()
        monkeypatch.setattr(
            "app.api.v1.auth.routes_service_accounts.get_secret_provider",
            lambda: fake_provider,
        )
        monkeypatch.setattr(
            "app.api.v1.auth.routes_service_accounts.get_nonce_store",
            lambda: RedisNonceStore(FakeRedis(server=fake_server)),
        )

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

        monkeypatch.setattr(
            "starter_console.services.auth.security.signing._build_vault_envelope",
            fake_envelope,
        )
        monkeypatch.setattr(
            "starter_console.services.auth.security.signing._vault_sign_payload",
            fake_sign,
        )

        def fake_build_vault_headers(
            payload: dict[str, Any], _settings: Any
        ) -> tuple[str, dict[str, str]]:
            envelope = fake_envelope(payload)
            payload_json = json.dumps(envelope, separators=(",", ":"))
            payload_b64 = (
                base64.urlsafe_b64encode(payload_json.encode("utf-8"))
                .decode("utf-8")
                .rstrip("=")
            )
            signature = fake_sign(payload_b64=payload_b64)
            return f"Bearer vault:{signature}", {"X-Vault-Payload": payload_b64}

        monkeypatch.setattr(
            "starter_console.services.auth.security.signing.build_vault_headers",
            fake_build_vault_headers,
        )
        monkeypatch.setattr(
            "starter_console.services.auth.tokens.build_vault_headers",
            fake_build_vault_headers,
        )

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
        assert fake_provider.calls, "Vault verification was not invoked."
        assert len(signed_payloads) == 1

        second_exit = handle_issue_service_account(args)
        second_output = capsys.readouterr()

        assert second_exit == 1
        assert (
            "error: Issuance failed (401): Vault payload nonce already used."
            in second_output.err
        )
        assert len(signed_payloads) == 2
        assert signed_payloads[0] == signed_payloads[1]

    config_module.get_settings.cache_clear()


def test_service_account_issue_returns_eddsa_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VAULT_VERIFY_ENABLED", "false")
    config_module.get_settings.cache_clear()

    payload = {
        "account": "analytics-batch",
        "scopes": ["conversations:read"],
        "tenant_id": "11111111-2222-3333-4444-555555555555",
        "lifetime_minutes": 30,
        "fingerprint": "contract-test",
        "force": True,
    }

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/service-accounts/issue",
            json=payload,
            headers={"Authorization": "Bearer dev-demo"},
        )

        assert response.status_code == 201, response.text
        body = response.json()
        verifier = get_token_verifier()
        claims = verifier.verify(body["refresh_token"])

        keyset = load_keyset()
        assert keyset.active is not None
        assert body["kid"] == keyset.active.kid
        assert claims["token_use"] == "refresh"
        assert claims["account"] == "analytics-batch"
        assert claims["tenant_id"] == payload["tenant_id"]

    config_module.get_settings.cache_clear()


def test_service_account_issue_rejects_vault_credential_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VAULT_VERIFY_ENABLED", "false")
    config_module.get_settings.cache_clear()

    payload = {
        "account": "analytics-batch",
        "scopes": ["conversations:read"],
        "tenant_id": "11111111-2222-3333-4444-555555555555",
    }

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/service-accounts/issue",
            json=payload,
            headers={
                "Authorization": "Bearer vault:forged",
                "X-Vault-Payload": "Zm9yZ2Vk",
            },
        )

        assert response.status_code == 503
        assert "Vault verification disabled" in response.text

    config_module.get_settings.cache_clear()
