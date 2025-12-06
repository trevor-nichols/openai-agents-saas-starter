from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest

from tests.smoke.http.auth import login_for_tokens
from tests.smoke.http.config import SmokeConfig, load_config
from tests.smoke.http.fixtures import apply_test_fixtures
from tests.smoke.http.state import SmokeState

pytestmark = pytest.mark.smoke


@pytest.fixture(scope="session")
def smoke_config() -> SmokeConfig:
    return load_config()


@pytest.fixture(scope="function")
async def http_client(smoke_config: SmokeConfig) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        base_url=smoke_config.base_url,
        timeout=smoke_config.request_timeout,
    ) as client:
        yield client


@pytest.fixture(scope="session")
async def smoke_seed(smoke_config: SmokeConfig) -> dict[str, Any]:
    """Apply deterministic fixtures and return the response payload (once per session)."""

    async with httpx.AsyncClient(
        base_url=smoke_config.base_url,
        timeout=smoke_config.request_timeout,
    ) as client:
        return await apply_test_fixtures(client, smoke_config)


@pytest.fixture(scope="function")
async def smoke_state(
    http_client: httpx.AsyncClient, smoke_config: SmokeConfig, smoke_seed: dict[str, Any]
) -> SmokeState:
    tenant_entry = smoke_seed["tenants"][smoke_config.tenant_slug]
    tenant_id = tenant_entry["tenant_id"]
    conversation_id = None
    if tenant_entry.get("conversations"):
        # Take the first conversation result (keys are conversation keys)
        conversation_id = next(iter(tenant_entry["conversations"].values()))["conversation_id"]

    tokens = await login_for_tokens(http_client, smoke_config, tenant_id)

    return SmokeState(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user_id=tokens.get("user_id"),
        session_id=tokens.get("session_id"),
    )
