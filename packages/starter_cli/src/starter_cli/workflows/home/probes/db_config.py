from __future__ import annotations

from urllib.parse import unquote, urlparse

from starter_cli.core.status_models import ProbeResult, ProbeState
from starter_cli.workflows.home.probes.registry import ProbeContext
from starter_cli.workflows.home.probes.util import simple_result

_LOCAL_DB_MODE_KEY = "STARTER_LOCAL_DATABASE_MODE"


def db_config_probe(ctx: ProbeContext) -> ProbeResult:
    """Validate local Docker Postgres config stays consistent with DATABASE_URL.

    This catches common drift where the compose port mapping or POSTGRES_DB creds
    are changed without regenerating DATABASE_URL (or vice-versa).
    """

    if ctx.profile != "demo":
        return ProbeResult(
            name="database_config",
            state=ProbeState.SKIPPED,
            detail="not a demo profile",
        )

    mode = (ctx.env.get(_LOCAL_DB_MODE_KEY) or "compose").strip().lower()
    if mode != "compose":
        return ProbeResult(
            name="database_config",
            state=ProbeState.SKIPPED,
            detail=f"{_LOCAL_DB_MODE_KEY}={mode}",
        )

    database_url = (ctx.env.get("DATABASE_URL") or "").strip()
    if not database_url:
        return simple_result(
            name="database_config",
            success=False,
            warn_on_failure=True,
            detail="DATABASE_URL not set (expected wizard-derived value for demo compose mode)",
            remediation="Run `starter_cli setup wizard --profile demo` to generate DATABASE_URL.",
        )

    expected = _expected_local_postgres(ctx)
    actual = _parse_database_url(database_url)
    mismatches = _diff_expected_vs_actual(expected, actual)

    if mismatches:
        detail = "; ".join(mismatches)
        remediation = (
            "Rerun the setup wizard to regenerate DATABASE_URL, or update POSTGRES_* "
            "to match the URL (and restart the compose stack)."
        )
        return simple_result(
            name="database_config",
            success=False,
            warn_on_failure=True,
            detail=detail,
            remediation=remediation,
            metadata={"expected": expected, "actual": actual},
        )

    return simple_result(
        name="database_config",
        success=True,
        detail="DATABASE_URL matches demo compose POSTGRES_* settings",
        metadata={"expected": expected},
    )


def _expected_local_postgres(ctx: ProbeContext) -> dict[str, object]:
    port_raw = (ctx.env.get("POSTGRES_PORT") or "5432").strip()
    try:
        port = int(port_raw)
    except ValueError:
        port = 5432
    return {
        "host": "localhost",
        "port": port,
        "username": (ctx.env.get("POSTGRES_USER") or "postgres").strip(),
        "password": (ctx.env.get("POSTGRES_PASSWORD") or "postgres").strip(),
        "database": (ctx.env.get("POSTGRES_DB") or "saas_starter_db").strip(),
    }


def _parse_database_url(url: str) -> dict[str, object]:
    parsed = urlparse(url)
    username = unquote(parsed.username or "")
    password = unquote(parsed.password or "")
    database = unquote((parsed.path or "").lstrip("/"))
    host = parsed.hostname or ""
    port = parsed.port or 5432
    return {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "database": database,
        "scheme": parsed.scheme,
    }


def _diff_expected_vs_actual(expected: dict[str, object], actual: dict[str, object]) -> list[str]:
    mismatches: list[str] = []

    host = str(actual.get("host") or "").strip().lower()
    if host and host not in {"localhost", "127.0.0.1"}:
        mismatches.append(f"DATABASE_URL host is {host!r} (expected localhost for compose mode)")

    if expected.get("port") != actual.get("port"):
        expected_port = expected.get("port")
        actual_port = actual.get("port")
        mismatches.append(
            f"port mismatch: POSTGRES_PORT={expected_port} vs DATABASE_URL port={actual_port}"
        )

    if expected.get("database") != actual.get("database"):
        expected_db = expected.get("database")
        actual_db = actual.get("database")
        mismatches.append(
            f"db mismatch: POSTGRES_DB={expected_db!r} vs DATABASE_URL db={actual_db!r}"
        )

    if expected.get("username") != actual.get("username"):
        expected_user = expected.get("username")
        actual_user = actual.get("username")
        mismatches.append(
            f"user mismatch: POSTGRES_USER={expected_user!r} vs DATABASE_URL user={actual_user!r}"
        )

    if expected.get("password") != actual.get("password"):
        # Avoid printing the actual password.
        mismatches.append("password mismatch between POSTGRES_PASSWORD and DATABASE_URL")

    return mismatches


__all__ = ["db_config_probe"]
