"""Contract tests for MFA endpoints with dependency overrides."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies.auth import require_current_user
from app.services.auth.mfa_service import get_mfa_service
import app.api.v1.auth.routes_mfa as mfa_module
from main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    previous_user = app.dependency_overrides.get(require_current_user)
    previous_service = app.dependency_overrides.get(get_mfa_service)

    def _stub_user():
        return {"user_id": str(uuid4()), "email": "user@example.com"}

    mock_service = AsyncMock()
    mock_service.list_methods.return_value = []
    mock_service.start_totp_enrollment.return_value = ("SECRET", uuid4())
    mock_service.verify_totp.return_value = None
    mock_service.regenerate_recovery_codes.return_value = ["code1", "code2"]
    mock_service.revoke_method.return_value = None

    app.dependency_overrides[require_current_user] = _stub_user
    mfa_module.get_mfa_service = lambda: mock_service
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        if previous_user is not None:
            app.dependency_overrides[require_current_user] = previous_user
        else:
            app.dependency_overrides.pop(require_current_user, None)
        if previous_service is not None:
            app.dependency_overrides[get_mfa_service] = previous_service
        else:
            app.dependency_overrides.pop(get_mfa_service, None)


def test_totp_enroll_verify(client: TestClient) -> None:
    resp = client.post("/api/v1/auth/mfa/totp/enroll")
    assert resp.status_code == 201
    method_id = resp.json()["method_id"]

    verify = client.post(
        "/api/v1/auth/mfa/totp/verify",
        json={"method_id": method_id, "code": "123456"},
    )
    assert verify.status_code == 200


def test_recovery_and_revoke(client: TestClient) -> None:
    recovery = client.post("/api/v1/auth/mfa/recovery/regenerate")
    assert recovery.status_code == 200
    assert len(recovery.json()["codes"]) == 2

    revoke = client.delete(f"/api/v1/auth/mfa/{uuid4()}")
    assert revoke.status_code == 200
