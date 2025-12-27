"""Contract tests covering the agent catalog + tooling endpoints."""

from __future__ import annotations

from typing import Any

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from tests.utils.contract_auth import make_user_payload, override_current_user
from tests.utils.contract_env import configure_contract_env

configure_contract_env()

pytestmark = pytest.mark.auto_migrations(enabled=True)

from app.infrastructure.db.engine import init_engine  # noqa: E402
from app.services.agents import AgentService  # noqa: E402
from main import app  # noqa: E402
from tests.utils.agent_contract import (  # noqa: E402
    default_agent_key,
    expected_tooling_flags_by_agent,
    expected_tools_by_agent,
    spec_index,
)


def _stub_current_user() -> dict[str, Any]:
    return make_user_payload()


@pytest_asyncio.fixture(autouse=True)
async def _ensure_engine_initialized() -> None:
    await init_engine(run_migrations=True)


@pytest.fixture(autouse=True)
def _override_current_user():
    with override_current_user(app, _stub_current_user):
        yield


@pytest.fixture(scope="function")
def client(_configure_agent_provider):
    with TestClient(app) as test_client:
        yield test_client


def test_list_available_agents(client: TestClient) -> None:
    response = client.get("/api/v1/agents")
    assert response.status_code == 200

    payload = response.json()
    assert "items" in payload
    assert isinstance(payload["items"], list)
    assert payload["total"] >= len(payload["items"])
    items = payload["items"]
    specs = spec_index()
    assert all(agent["name"] in specs for agent in items)
    assert any(agent["name"] == default_agent_key() for agent in items)
    expected_tooling = expected_tooling_flags_by_agent()
    for agent in items:
        if agent.get("output_schema") is not None:
            assert isinstance(agent["output_schema"], dict)
        tooling = agent.get("tooling")
        assert isinstance(tooling, dict)
        assert tooling == expected_tooling[agent["name"]]


def test_list_available_agents_pagination(client: TestClient) -> None:
    first = client.get("/api/v1/agents?limit=2")
    assert first.status_code == 200
    first_payload = first.json()

    assert len(first_payload["items"]) <= 2
    assert first_payload["total"] >= len(first_payload["items"])

    next_cursor = first_payload.get("next_cursor")
    if first_payload["total"] > len(first_payload["items"]):
        assert next_cursor is not None
        second = client.get(f"/api/v1/agents?cursor={next_cursor}&limit=2")
        assert second.status_code == 200
        second_payload = second.json()
        assert len(second_payload["items"]) <= 2
        # Ensure we advanced the cursor
        assert set(a["name"] for a in second_payload["items"]).isdisjoint(
            set(a["name"] for a in first_payload["items"])
        )
    else:
        assert next_cursor is None


def test_list_available_agents_invalid_cursor(client: TestClient) -> None:
    response = client.get("/api/v1/agents?cursor=not-a-cursor")
    assert response.status_code == 400


def test_list_available_agents_invalid_limit(client: TestClient) -> None:
    response = client.get("/api/v1/agents?limit=0")
    assert response.status_code == 422  # validation rejects at FastAPI layer


def test_get_agent_status(client: TestClient) -> None:
    agent_key = default_agent_key()
    response = client.get(f"/api/v1/agents/{agent_key}/status")
    assert response.status_code == 200

    payload = response.json()
    assert payload["name"] == agent_key
    assert payload["status"] == "active"
    assert "output_schema" in payload
    expected_tooling = expected_tooling_flags_by_agent()
    assert payload["tooling"] == expected_tooling[agent_key]


def test_get_nonexistent_agent_status(client: TestClient) -> None:
    response = client.get("/api/v1/agents/nonexistent/status")
    assert response.status_code == 404


def test_tools_endpoint_returns_per_agent_tooling(client: TestClient) -> None:
    response = client.get("/api/v1/tools")
    assert response.status_code == 200

    payload = response.json()
    assert "per_agent" in payload
    per_agent = payload["per_agent"]
    expected = expected_tools_by_agent()
    assert expected.keys() <= per_agent.keys()
    for agent, tools in expected.items():
        assert set(per_agent[agent]) == tools


def test_agent_service_initialization(agent_service: AgentService) -> None:
    page = agent_service.list_available_agents_page(limit=10, cursor=None, search=None)
    names = {agent.name for agent in page.items}

    expected_names = set(spec_index().keys())
    assert expected_names.issubset(names)
    assert default_agent_key() in names
