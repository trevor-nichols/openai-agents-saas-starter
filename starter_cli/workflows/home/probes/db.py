from __future__ import annotations

import asyncio
import os
from urllib.parse import urlparse

from starter_cli.core.status_models import ProbeResult
from starter_cli.workflows.home.probes.util import simple_result, tcp_check

try:  # optional dependency; backend already uses asyncpg
    import asyncpg
except Exception:  # pragma: no cover - optional import
    asyncpg = None


def db_probe(*, warn_only: bool = False) -> ProbeResult:
    url = os.getenv("DATABASE_URL")
    if not url:
        return simple_result(
            name="database",
            success=False,
            warn_on_failure=False,
            detail="DATABASE_URL not set",
            remediation="Populate DATABASE_URL via setup wizard or env file.",
        )

    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    if not scheme.startswith("postgres"):
        return simple_result(
            name="database",
            success=False,
            warn_on_failure=True,
            detail=f"Unsupported DATABASE_URL scheme '{scheme or 'unknown'}' (expected postgres)",
            remediation="Point DATABASE_URL to Postgres (postgresql://...)",
            metadata={"scheme": scheme},
        )

    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    tcp_ok, tcp_detail = tcp_check(host, port, timeout=0.75)

    ping_ok: bool | None = None
    ping_detail: str | None = None
    if tcp_ok:
        ping_ok, ping_detail = _pg_ping(url, timeout=1.5)

    success = tcp_ok and (ping_ok is not False)
    # Promote to WARN when we had to skip ping; ERROR when ping fails.
    warn_on_failure = ping_ok is None or warn_only
    detail = "; ".join(
        part for part in (f"tcp={tcp_detail}", f"ping={ping_detail}") if part
    )
    remediation = "Ensure Postgres is running and reachable; run migrations if needed."
    return simple_result(
        name="database",
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


def _pg_ping(url: str, *, timeout: float = 1.5) -> tuple[bool | None, str]:
    """Lightweight Postgres ping using asyncpg when available.

    Returns (ok|False|None, detail). ``None`` means ping skipped (asyncpg unavailable).
    """

    if asyncpg is None:
        return None, "asyncpg not installed; ping skipped"

    async def _run_ping() -> str:
        assert asyncpg is not None
        conn = await asyncpg.connect(dsn=url, timeout=int(timeout))
        try:
            await conn.execute("SELECT 1")
            return "select 1 ok"
        finally:
            await conn.close()

    try:
        _run_coro(_run_ping(), timeout=timeout + 0.5)
        return True, "select 1 ok"
    except Exception as exc:  # pragma: no cover - exercised via tests by monkeypatch
        return False, f"pg ping failed: {exc.__class__.__name__}: {exc}"


def _run_coro(coro, *, timeout: float | None = None) -> object:
    """Run a coroutine with an isolated event loop."""

    try:
        return asyncio.run(asyncio.wait_for(coro, timeout=timeout))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(asyncio.wait_for(coro, timeout=timeout))
        finally:
            loop.close()


__all__ = ["db_probe"]
