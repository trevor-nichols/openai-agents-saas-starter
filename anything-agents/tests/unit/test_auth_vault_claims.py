import pytest
from fastapi import HTTPException, status

from app.api.models.auth import ServiceAccountIssueRequest
from app.api.v1.auth.router import _validate_claims_against_request


def _base_claims(**overrides):
    claims = {
        "iss": "vault-transit",
        "aud": ["auth-service"],
        "sub": "service-account-cli",
        "nonce": "abc",
        "iat": 1,
        "exp": 999999999,
        "account": "ci-bot",
        "tenant_id": None,
        "scopes": ["agents:read"],
    }
    claims.update(overrides)
    return claims


def _request(**overrides):
    payload = ServiceAccountIssueRequest(
        account="ci-bot",
        scopes=["agents:read"],
        tenant_id=None,
        lifetime_minutes=None,
        fingerprint=None,
        force=False,
    )
    for key, value in overrides.items():
        setattr(payload, key, value)
    return payload


def test_scope_mismatch_raises():
    claims = _base_claims(scopes=["agents:read"])
    request = _request(scopes=["agents:read", "billing:write"])
    with pytest.raises(HTTPException) as exc:
        _validate_claims_against_request(claims, request)
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST


def test_scopes_match_even_if_order_diff():
    claims = _base_claims(scopes=["billing:write", "agents:read"])
    request = _request(scopes=["agents:read", "billing:write"])
    _validate_claims_against_request(claims, request)
    # normalized scopes copy from claims order
    assert request.scopes == ["billing:write", "agents:read"]


def test_ttl_mismatch_rejected():
    claims = _base_claims(scopes=["agents:read"], lifetime_minutes=30)
    request = _request(lifetime_minutes=15)
    with pytest.raises(HTTPException) as exc:
        _validate_claims_against_request(claims, request)
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST


def test_fingerprint_mismatch_rejected():
    claims = _base_claims(scopes=["agents:read"], fingerprint="runner-a")
    request = _request(fingerprint="runner-b")
    with pytest.raises(HTTPException) as exc:
        _validate_claims_against_request(claims, request)
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST


def test_claims_backfill_missing_request_fields():
    claims = _base_claims(
        scopes=["agents:read"], lifetime_minutes=45, fingerprint="runner-a"
    )
    request = _request()
    _validate_claims_against_request(claims, request)
    assert request.lifetime_minutes == 45
    assert request.fingerprint == "runner-a"
