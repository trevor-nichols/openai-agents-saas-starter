"""Contract tests for user consent endpoints with dependency overrides."""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, UTC
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies.auth import require_current_user
from app.services.consent_service import get_consent_service
import app.api.v1.users.routes_consents as consents_module
from main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    prev_user = app.dependency_overrides.get(require_current_user)
    prev_service = app.dependency_overrides.get(get_consent_service)

    def _user():
        return {"user_id": str(uuid4())}

    consent = AsyncMock()
    consent.record.return_value = None

    class Obj:
        def __init__(self):
            self.policy_key = "tos"
            self.version = "v1"
            self.accepted_at = datetime.now(UTC)

    consent.list_for_user.return_value = [Obj()]

    app.dependency_overrides[require_current_user] = _user
    consents_module.get_consent_service = lambda: consent
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        if prev_user is not None:
            app.dependency_overrides[require_current_user] = prev_user
        else:
            app.dependency_overrides.pop(require_current_user, None)
        if prev_service is not None:
            app.dependency_overrides[get_consent_service] = prev_service
        else:
            app.dependency_overrides.pop(get_consent_service, None)


def test_record_consent(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/users/consents",
        json={"policy_key": "tos", "version": "v1"},
    )
    assert resp.status_code == 201


def test_list_consents(client: TestClient) -> None:
    resp = client.get("/api/v1/users/consents")
    assert resp.status_code == 200
    assert resp.json()[0]["policy_key"] == "tos"
