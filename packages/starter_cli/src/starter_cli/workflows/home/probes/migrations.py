from __future__ import annotations

import os
from pathlib import Path

from starter_cli.core.constants import PROJECT_ROOT
from starter_cli.core.status_models import ProbeResult, ProbeState
from starter_cli.workflows.home.probes.db import _pg_ping  # reuse db connectivity helper

VERSIONS_DIR = PROJECT_ROOT / "apps" / "api-service" / "alembic" / "versions"
ALEMBIC_INI = PROJECT_ROOT / "apps" / "api-service" / "alembic.ini"


def migrations_probe() -> ProbeResult:
    if not VERSIONS_DIR.exists():
        return ProbeResult(
            name="migrations",
            state=ProbeState.WARN,
            detail="alembic/versions missing",
            remediation="Verify repo checkout includes migrations or regenerate via alembic.",
        )

    local_heads = _head_revisions(VERSIONS_DIR)
    if not local_heads:
        return ProbeResult(
            name="migrations",
            state=ProbeState.WARN,
            detail="No migration files present",
            remediation="Generate an initial migration via Alembic.",
        )
    local_head = sorted(local_heads)[-1]

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return ProbeResult(
            name="migrations",
            state=ProbeState.WARN,
            detail="DATABASE_URL not set; cannot compare DB head",
            remediation="Set DATABASE_URL then rerun doctor.",
            metadata={"local_head": local_head},
        )

    db_revision, db_detail = _db_revision(db_url)
    if db_revision is None:
        return ProbeResult(
            name="migrations",
            state=ProbeState.WARN,
            detail=db_detail or "Unable to read alembic_version",
            remediation="Ensure the DB is reachable and migrations applied.",
            metadata={"local_head": local_head},
        )

    if db_revision in local_heads:
        return ProbeResult(
            name="migrations",
            state=ProbeState.OK,
            detail=f"DB at head {db_revision}",
            metadata={"local_heads": local_heads, "db_revision": db_revision},
        )

    return ProbeResult(
        name="migrations",
        state=ProbeState.WARN,
        detail=f"DB at {db_revision}, code at {local_head}",
        remediation="Run migrations (just migrate) so DB matches code.",
        metadata={"local_heads": local_heads, "db_revision": db_revision},
    )


def _head_revisions(versions_dir: Path) -> list[str]:
    """
    Return the current head revision(s) according to Alembic.

    Prefer Alembic's ScriptDirectory (authoritative for heads/branches) to
    avoid lexicographic mistakes on filenames (e.g., hex IDs vs timestamps).
    """

    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        cfg = Config(str(ALEMBIC_INI))
        cfg.set_main_option("script_location", str(VERSIONS_DIR.parent))
        script_dir = ScriptDirectory.from_config(cfg)
        heads = script_dir.get_heads()
        if heads:
            return list(heads)
    except Exception:
        # Fallback: filename sort (best-effort)
        versions = sorted(
            (p for p in versions_dir.glob("*.py") if p.is_file()),
            key=lambda p: p.name,
            reverse=True,
        )
        if not versions:
            return []
        stems = []
        for p in versions:
            stem = p.stem
            stems.append(stem.split("_")[0] if "_" in stem else stem)
        return stems

    return []


def _db_revision(db_url: str) -> tuple[str | None, str | None]:
    """Fetch the current alembic revision from the database.

    Returns (revision|None, detail). None means unknown/unavailable.
    """

    ok, detail = _pg_ping(db_url)
    if ok is False:
        return None, detail

    try:
        import asyncpg
    except Exception:  # pragma: no cover - same fallback as _pg_ping
        return None, "asyncpg not installed; cannot read alembic_version"

    try:
        from starter_cli.workflows.home.probes.db import _normalize_db_url
    except Exception:  # pragma: no cover - defensive import
        _normalize_db_url = lambda u: u  # type: ignore

    async def _fetch_rev() -> str | None:
        conn = await asyncpg.connect(dsn=_normalize_db_url(db_url), timeout=2)
        try:
            row = await conn.fetchrow("SELECT version_num FROM alembic_version LIMIT 1;")
            return row["version_num"] if row else None
        finally:
            await conn.close()

    try:
        import asyncio

        rev = asyncio.run(_fetch_rev())
        if rev is None:
            return None, "alembic_version table empty"
        return str(rev), "ok"
    except Exception as exc:  # pragma: no cover - exercised via monkeypatch
        return None, f"failed to read alembic_version: {exc.__class__.__name__}: {exc}"


__all__ = ["migrations_probe"]
