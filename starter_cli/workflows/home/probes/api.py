from __future__ import annotations

import os
from urllib.parse import urljoin

from starter_cli.core.status_models import ProbeResult
from starter_cli.workflows.home.probes.util import http_check, simple_result


def api_probe(*, warn_only: bool = False) -> ProbeResult:
    base = os.getenv("API_BASE_URL") or "http://localhost:8000"
    url = urljoin(base.rstrip("/") + "/", "api/v1/health/ready")
    ok, detail, status = http_check(url)
    if not ok:
        # fallback to older path if present
        fallback = urljoin(base.rstrip("/") + "/", "health/ready")
        ok, detail, status = http_check(fallback)
        url = fallback

    return simple_result(
        name="api",
        success=ok,
        warn_on_failure=warn_only,
        detail=detail,
        remediation="Start the FastAPI server (hatch run serve) or fix API_BASE_URL.",
        metadata={"url": url, "status": status},
    )


__all__ = ["api_probe"]
