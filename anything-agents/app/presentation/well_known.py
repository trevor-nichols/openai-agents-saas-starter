"""Presentation layer for /.well-known surfaces."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.keys import load_keyset

router = APIRouter()


@router.get("/.well-known/jwks.json", include_in_schema=False)
async def jwks_document() -> JSONResponse:
    """Expose current public signing keys for downstream verifiers."""

    settings = get_settings()
    keyset = load_keyset(settings)
    jwks = keyset.to_jwks()
    headers = {"Cache-Control": f"public, max-age={settings.auth_jwks_cache_seconds}"}
    return JSONResponse(jwks, headers=headers)

