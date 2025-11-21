from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

from starter_cli.core.status_models import ProbeResult
from starter_cli.workflows.home.probes.util import simple_result, tcp_check

try:
    import redis
except Exception:  # pragma: no cover - optional dependency
    redis = None  # type: ignore[assignment]


def redis_probe() -> ProbeResult:
    url = os.getenv("RATE_LIMIT_REDIS_URL") or os.getenv("REDIS_URL")
    if not url:
        return simple_result(
            name="redis",
            success=False,
            warn_on_failure=False,
            detail="REDIS_URL not set",
            remediation="Set REDIS_URL (or RATE_LIMIT_REDIS_URL) via wizard or env files.",
        )

    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    if not scheme.startswith("redis"):
        return simple_result(
            name="redis",
            success=False,
            warn_on_failure=True,
            detail=f"Unsupported REDIS_URL scheme '{scheme or 'unknown'}' (expected redis/rediss)",
            remediation="Point REDIS_URL to Redis (redis:// or rediss://).",
            metadata={"scheme": scheme},
        )

    host = parsed.hostname or "localhost"
    port = parsed.port or 6379
    tcp_ok, tcp_detail = tcp_check(host, port, timeout=0.5)
    ping_ok: bool | None = None
    ping_detail: str | None = None
    if tcp_ok:
        ping_ok, ping_detail = _redis_ping(url)

    success = tcp_ok and (ping_ok is not False)
    warn_on_failure = ping_ok is None
    detail = "; ".join(part for part in (f"tcp={tcp_detail}", f"ping={ping_detail}") if part)
    remediation = "Ensure Redis is running and reachable at configured URL."
    return simple_result(
        name="redis",
        success=success,
        warn_on_failure=warn_on_failure,
        detail=detail or "checked",
        remediation=remediation,
        metadata={
            "host": host,
            "port": port,
            "ping": "skipped" if ping_ok is None else ("ok" if ping_ok else "failed"),
        },
    )


def _redis_ping(url: str, *, timeout: float = 1.0) -> tuple[bool | None, str]:
    """Ping Redis using the redis client if available.

    Returns (ok|False|None, detail). ``None`` means ping skipped.
    """

    if redis is None:
        return None, "redis package not installed; ping skipped"

    try:
        client = redis.Redis.from_url(
            url, socket_connect_timeout=timeout, socket_timeout=timeout
        )
        client.ping()
        return True, "PING ok"
    except Exception as exc:  # pragma: no cover - covered via monkeypatch in tests
        return False, f"redis ping failed: {exc.__class__.__name__}: {exc}"


__all__ = ["redis_probe"]
