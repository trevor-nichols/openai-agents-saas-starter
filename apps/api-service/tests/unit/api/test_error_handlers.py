from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.errors import register_exception_handlers


def test_http_exception_returns_error_envelope() -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    def boom() -> dict[str, str]:
        raise HTTPException(
            status_code=403,
            detail={"code": "Forbidden", "message": "Nope", "details": {"reason": "policy"}},
        )

    client = TestClient(app)
    response = client.get("/boom")
    assert response.status_code == 403
    payload: dict[str, Any] = response.json()
    assert payload["success"] is False
    assert payload["error"] == "Forbidden"
    assert payload["message"] == "Nope"
    assert payload["details"] == {"reason": "policy"}
    assert "detail" not in payload


def test_unhandled_exception_returns_error_envelope() -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/crash")
    def crash() -> dict[str, str]:
        raise RuntimeError("kaboom")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/crash")
    assert response.status_code == 500
    payload: dict[str, Any] = response.json()
    assert payload["success"] is False
    assert payload["error"] == "InternalServerError"
    assert payload["message"] == "Internal server error."
    assert payload.get("details") is None
    assert "detail" not in payload
