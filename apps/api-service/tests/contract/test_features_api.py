"""Contract tests for feature snapshot endpoints."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.utils.contract_auth import make_user_payload

from app.api.dependencies.auth import require_current_user
from app.api.v1.features import router as features_router
from app.domain.feature_flags import FeatureSnapshot
from app.services.feature_flags import get_feature_flag_service


def _stub_user() -> dict[str, Any]:
    return make_user_payload(roles=("viewer",))


class _StubFeatureFlagService:
    async def snapshot_for_tenant(self, tenant_id: str) -> FeatureSnapshot:
        return FeatureSnapshot(billing_enabled=False, billing_stream_enabled=False)


def _stub_feature_service() -> _StubFeatureFlagService:
    return _StubFeatureFlagService()


def _build_client() -> Generator[TestClient, None, None]:
    app = FastAPI()
    app.include_router(features_router.router, prefix="/api/v1")
    app.dependency_overrides[require_current_user] = _stub_user
    app.dependency_overrides[get_feature_flag_service] = _stub_feature_service
    with TestClient(app) as client:
        yield client


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    yield from _build_client()


def test_feature_snapshot_contract(client: TestClient) -> None:
    response = client.get("/api/v1/features")
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "billing_enabled": False,
        "billing_stream_enabled": False,
    }
