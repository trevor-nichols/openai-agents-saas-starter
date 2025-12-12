from __future__ import annotations

import importlib
import logging
from typing import Any

import pytest

from app.core.settings import get_settings


def _build_openapi_schema(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    # Avoid noisy/shutdown-unsafe tracing logs from the Agents SDK during tests.
    monkeypatch.setenv("OPENAI_AGENTS_DISABLE_TRACING", "true")
    logging.getLogger("openai.agents").setLevel(logging.CRITICAL)

    # Enable the conditional routers so the contract is complete.
    monkeypatch.setenv("ENABLE_BILLING", "true")
    monkeypatch.setenv("ENABLE_BILLING_STREAM", "true")
    monkeypatch.setenv("ENABLE_FRONTEND_LOG_INGEST", "true")
    get_settings.cache_clear()

    # Some routers are conditionally included at module import time; reload them
    # after toggling env vars so the OpenAPI surface is complete even when other
    # tests imported the modules earlier in the session.
    import app.api.v1.router as v1_router_module
    import app.api.router as api_router_module

    importlib.reload(v1_router_module)
    importlib.reload(api_router_module)

    # Import after env is set. Reload to avoid any previous module-level state.
    main = importlib.import_module("main")
    importlib.reload(main)

    app = main.create_application()
    return app.openapi()


def test_openapi_declares_sse_streams(monkeypatch: pytest.MonkeyPatch) -> None:
    schema = _build_openapi_schema(monkeypatch)

    activity_response = schema["paths"]["/api/v1/activity/stream"]["get"]["responses"]["200"]
    activity_content = activity_response["content"]
    assert "text/event-stream" in activity_content
    assert "Heartbeats" in activity_response.get("description", "")
    assert "data:" in activity_response.get("description", "")

    billing_response = schema["paths"]["/api/v1/billing/stream"]["get"]["responses"]["200"]
    billing_content = billing_response["content"]
    assert "text/event-stream" in billing_content
    assert "Heartbeats" in billing_response.get("description", "")
    assert "data:" in billing_response.get("description", "")


def test_openapi_declares_binary_downloads(monkeypatch: pytest.MonkeyPatch) -> None:
    schema = _build_openapi_schema(monkeypatch)

    for path in (
        "/api/v1/openai/files/{file_id}/download",
        "/api/v1/openai/containers/{container_id}/files/{file_id}/download",
    ):
        resp = schema["paths"][path]["get"]["responses"]["200"]
        assert "application/octet-stream" in resp["content"]
        schema_obj = resp["content"]["application/octet-stream"]["schema"]
        assert schema_obj.get("format") == "binary"
        headers = resp.get("headers") or {}
        assert "Content-Disposition" in headers
        assert "Cache-Control" in headers


def test_openapi_declares_rss(monkeypatch: pytest.MonkeyPatch) -> None:
    schema = _build_openapi_schema(monkeypatch)
    resp = schema["paths"]["/api/v1/status/rss"]["get"]["responses"]["200"]
    assert "application/rss+xml" in resp["content"]


def test_openapi_declares_raw_body_endpoints(monkeypatch: pytest.MonkeyPatch) -> None:
    schema = _build_openapi_schema(monkeypatch)

    stripe = schema["paths"]["/webhooks/stripe"]["post"]
    assert stripe["requestBody"]["required"] is True
    assert "application/octet-stream" in stripe["requestBody"]["content"]
    assert "application/json" in stripe["requestBody"]["content"]
    header_params = [p for p in stripe.get("parameters", []) if p.get("in") == "header"]
    assert any(p.get("name") == "stripe-signature" and p.get("required") for p in header_params)

    logs = schema["paths"]["/api/v1/logs"]["post"]
    assert logs["requestBody"]["required"] is True
    assert "application/json" in logs["requestBody"]["content"]
    log_header_params = [p for p in logs.get("parameters", []) if p.get("in") == "header"]
    assert any(p.get("name") == "x-log-signature" and p.get("required") for p in log_header_params)


def test_openapi_tools_and_vector_search_are_typed(monkeypatch: pytest.MonkeyPatch) -> None:
    schema = _build_openapi_schema(monkeypatch)

    tools_schema = schema["paths"]["/api/v1/tools"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    assert tools_schema == {"$ref": "#/components/schemas/ToolCatalogResponse"}

    search_schema = schema["paths"]["/api/v1/vector-stores/{vector_store_id}/search"]["post"][
        "responses"
    ]["200"]["content"]["application/json"]["schema"]
    assert search_schema == {"$ref": "#/components/schemas/VectorStoreSearchResponse"}

def test_openapi_uses_validation_error_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    schema = _build_openapi_schema(monkeypatch)

    assert "ValidationErrorResponse" in schema["components"]["schemas"]

    # Ensure we don't advertise FastAPI's default validation error schema.
    refs = str(schema)
    assert "HTTPValidationError" not in refs

    # Spot-check at least one route's 422 points to our envelope.
    responses = schema["paths"]["/api/v1/workflows/runs/{run_id}/cancel"]["post"]["responses"]
    assert responses["422"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ValidationErrorResponse"
    }
