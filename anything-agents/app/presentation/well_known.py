"""Presentation layer for /.well-known surfaces."""

from __future__ import annotations

import hashlib
from email.utils import format_datetime

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.keys import load_keyset
from app.observability.metrics import JWKS_NOT_MODIFIED_TOTAL, JWKS_REQUESTS_TOTAL

router = APIRouter()


@router.get("/.well-known/jwks.json", include_in_schema=False)
async def jwks_document(request: Request) -> Response:
    """Expose current public signing keys for downstream verifiers."""

    settings = get_settings()
    keyset = load_keyset(settings)
    document = keyset.materialize_jwks()
    etag = _build_etag(document.fingerprint, settings.auth_jwks_etag_salt)
    headers = {
        "Cache-Control": f"public, max-age={settings.jwks_max_age_seconds}",
        "ETag": etag,
        "Last-Modified": format_datetime(document.last_modified, usegmt=True),
    }

    if request.headers.get("if-none-match") == etag:
        JWKS_NOT_MODIFIED_TOTAL.inc()
        JWKS_REQUESTS_TOTAL.inc()
        return Response(status_code=304, headers=headers)

    JWKS_REQUESTS_TOTAL.inc()
    return JSONResponse(document.payload, headers=headers)


def _build_etag(fingerprint: str, salt: str) -> str:
    material = f"{salt}:{fingerprint}".encode()
    digest = hashlib.sha256(material).hexdigest()
    return f'"{digest}"'
