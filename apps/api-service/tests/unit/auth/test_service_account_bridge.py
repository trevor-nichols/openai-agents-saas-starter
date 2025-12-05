from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.api.dependencies.service_accounts import ServiceAccountActor, ServiceAccountActorType
from app.api.models.auth import BrowserServiceAccountIssueRequest
from app.services.auth.errors import ServiceAccountError
from app.services.service_account_bridge import (
    BrowserIssuanceError,
    ServiceAccountIssuanceBridge,
    SignedVaultPayload,
)


@pytest.fixture(autouse=True)
def _stub_bridge_auth(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Prevent tests from instantiating the real AuthService stack."""

    stub = SimpleNamespace(issue_service_account_refresh_token=AsyncMock())
    monkeypatch.setattr("app.services.service_account_bridge.auth_service", stub)
    return stub


class _StubSigner:
    def __init__(self, payload: SignedVaultPayload) -> None:
        self.payload = payload

    async def sign(self, payload: dict[str, Any]) -> SignedVaultPayload:
        assert payload["account"] == "ci"
        return self.payload


@pytest.mark.asyncio
async def test_issue_from_browser_calls_auth_service(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = BrowserServiceAccountIssueRequest(
        account="ci",
        scopes=["conversations:read"],
        tenant_id="tenant-1",
        lifetime_minutes=30,
        fingerprint="runner-1",
        force=False,
        reason="Rotate weekly credentials",
    )
    signer = _StubSigner(SignedVaultPayload(payload_b64="payload", signature="vault:v1:sig"))
    bridge = ServiceAccountIssuanceBridge(signer=signer)

    mock_issue = AsyncMock(return_value={"refresh_token": "rt", "account": "ci"})
    monkeypatch.setattr(
        "app.services.service_account_bridge.auth_service.issue_service_account_refresh_token",
        mock_issue,
    )
    monkeypatch.setattr(
        "app.services.service_account_bridge.log_event",
        lambda *args, **kwargs: None,
    )

    actor = ServiceAccountActor(
        actor_type=ServiceAccountActorType.TENANT_ADMIN,
        tenant_id="tenant-1",
        user={"payload": {"sub": "user-123"}},
    )

    result = await bridge.issue_from_browser(actor=actor, request=payload)

    assert result["account"] == "ci"
    mock_issue.assert_awaited_once_with(
        account="ci",
        scopes=["conversations:read"],
        tenant_id="tenant-1",
        requested_ttl_minutes=30,
        fingerprint="runner-1",
        force=False,
    )


@pytest.mark.asyncio
async def test_issue_from_browser_requires_reason() -> None:
    bridge = ServiceAccountIssuanceBridge(signer=_StubSigner(SignedVaultPayload("", "")))
    actor = ServiceAccountActor(
        actor_type=ServiceAccountActorType.TENANT_ADMIN,
        tenant_id="tenant-1",
        user={"payload": {"sub": "user-123"}},
    )
    payload = BrowserServiceAccountIssueRequest(
        account="ci",
        scopes=["conversations:read"],
        tenant_id="tenant-1",
        lifetime_minutes=None,
        fingerprint=None,
        force=False,
        reason="          ",
    )

    with pytest.raises(BrowserIssuanceError):
        await bridge.issue_from_browser(actor=actor, request=payload)


@pytest.mark.asyncio
async def test_issue_from_browser_defaults_tenant_id(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = BrowserServiceAccountIssueRequest(
        account="ci",
        scopes=["conversations:read"],
        tenant_id=None,
        lifetime_minutes=15,
        fingerprint=None,
        force=False,
        reason="Rotate CI token",
    )
    signer = _StubSigner(SignedVaultPayload(payload_b64="payload", signature="vault:v1:sig"))
    bridge = ServiceAccountIssuanceBridge(signer=signer)

    mock_issue = AsyncMock(return_value={"refresh_token": "rt", "account": "ci"})
    monkeypatch.setattr(
        "app.services.service_account_bridge.auth_service.issue_service_account_refresh_token",
        mock_issue,
    )
    monkeypatch.setattr(
        "app.services.service_account_bridge.log_event",
        lambda *args, **kwargs: None,
    )

    actor = ServiceAccountActor(
        actor_type=ServiceAccountActorType.TENANT_ADMIN,
        tenant_id="tenant-1",
        user={"payload": {"sub": "user-123"}},
    )

    await bridge.issue_from_browser(actor=actor, request=payload)

    mock_issue.assert_awaited_once_with(
        account="ci",
        scopes=["conversations:read"],
        tenant_id="tenant-1",
        requested_ttl_minutes=15,
        fingerprint=None,
        force=False,
    )


@pytest.mark.asyncio
async def test_issue_from_browser_rejects_cross_tenant() -> None:
    payload = BrowserServiceAccountIssueRequest(
        account="ci",
        scopes=["conversations:read"],
        tenant_id="tenant-2",
        lifetime_minutes=15,
        fingerprint=None,
        force=False,
        reason="Rotate CI token",
    )
    bridge = ServiceAccountIssuanceBridge(signer=_StubSigner(SignedVaultPayload("", "")))
    actor = ServiceAccountActor(
        actor_type=ServiceAccountActorType.TENANT_ADMIN,
        tenant_id="tenant-1",
        user={"payload": {"sub": "user-123"}},
    )

    with pytest.raises(BrowserIssuanceError) as excinfo:
        await bridge.issue_from_browser(actor=actor, request=payload)

    assert "Tenant mismatch" in str(excinfo.value)


@pytest.mark.asyncio
async def test_issue_from_browser_maps_service_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = BrowserServiceAccountIssueRequest(
        account="ci",
        scopes=["conversations:read"],
        tenant_id="tenant-1",
        lifetime_minutes=15,
        fingerprint=None,
        force=False,
        reason="Rotate CI token",
    )
    signer = _StubSigner(SignedVaultPayload(payload_b64="payload", signature="vault:v1:sig"))
    bridge = ServiceAccountIssuanceBridge(signer=signer)

    async def _raise(*_args: Any, **_kwargs: Any) -> None:
        raise ServiceAccountError("boom")

    monkeypatch.setattr(
        "app.services.service_account_bridge.auth_service.issue_service_account_refresh_token",
        _raise,
    )

    actor = ServiceAccountActor(
        actor_type=ServiceAccountActorType.TENANT_ADMIN,
        tenant_id="tenant-1",
        user={"payload": {"sub": "user-123"}},
    )

    with pytest.raises(BrowserIssuanceError) as excinfo:
        await bridge.issue_from_browser(actor=actor, request=payload)

    assert excinfo.value.status_code == 503
    assert "Failed to issue service-account token" in str(excinfo.value)
