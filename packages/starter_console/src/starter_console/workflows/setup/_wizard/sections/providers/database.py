from __future__ import annotations

import os
from urllib.parse import quote, urlparse

from starter_console.core import CLIError

from ....inputs import InputProvider
from ...context import WizardContext
from .._prompts import prompt_nonempty_string, prompt_port

_LOCAL_DB_MODE_KEY = "STARTER_LOCAL_DATABASE_MODE"
_LOCAL_DB_MODES = ("compose", "external")


def collect_database(context: WizardContext, provider: InputProvider) -> None:
    if context.profile == "demo":
        _collect_local_database(context, provider)
        return

    db_url = provider.prompt_string(
        key="DATABASE_URL",
        prompt="Primary Postgres connection URL (DATABASE_URL)",
        default=context.current("DATABASE_URL") or os.getenv("DATABASE_URL"),
        required=True,
    ).strip()
    if not db_url:
        raise CLIError("DATABASE_URL is required outside demo profiles.")
    context.set_backend("DATABASE_URL", db_url)


def _collect_local_database(context: WizardContext, provider: InputProvider) -> None:
    existing_url = (context.current("DATABASE_URL") or os.getenv("DATABASE_URL") or "").strip()
    existing_mode = (context.current(_LOCAL_DB_MODE_KEY) or "").strip().lower()
    if existing_mode not in _LOCAL_DB_MODES:
        existing_mode = _infer_local_db_mode(existing_url)

    mode = provider.prompt_choice(
        key=_LOCAL_DB_MODE_KEY,
        prompt="Local database mode",
        choices=_LOCAL_DB_MODES,
        default=existing_mode or "compose",
    ).strip()
    if mode not in _LOCAL_DB_MODES:  # pragma: no cover - provider enforces choices
        raise CLIError(f"{_LOCAL_DB_MODE_KEY} must be one of {', '.join(_LOCAL_DB_MODES)}.")

    context.set_backend(_LOCAL_DB_MODE_KEY, mode)
    if mode == "external":
        db_url = provider.prompt_string(
            key="DATABASE_URL",
            prompt="Primary Postgres connection URL (DATABASE_URL)",
            default=existing_url or None,
            required=True,
        ).strip()
        if not db_url:
            raise CLIError("DATABASE_URL is required when STARTER_LOCAL_DATABASE_MODE=external.")
        context.set_backend("DATABASE_URL", db_url)
        return

    # STARTER_LOCAL_DATABASE_MODE=compose: manage Docker Postgres inputs and derive DATABASE_URL.
    port = prompt_port(
        context,
        provider,
        key="POSTGRES_PORT",
        prompt="Local Postgres port (host)",
        default=context.current("POSTGRES_PORT") or "5432",
    )
    user = prompt_nonempty_string(
        context,
        provider,
        key="POSTGRES_USER",
        prompt="Local Postgres username",
        default=context.current("POSTGRES_USER") or "postgres",
    )
    password = provider.prompt_secret(
        key="POSTGRES_PASSWORD",
        prompt="Local Postgres password",
        existing=context.current("POSTGRES_PASSWORD") or "postgres",
        required=True,
    )
    db_name = prompt_nonempty_string(
        context,
        provider,
        key="POSTGRES_DB",
        prompt="Local Postgres database name",
        default=context.current("POSTGRES_DB") or "saas_starter_db",
    )

    context.set_backend("POSTGRES_PORT", str(port))
    context.set_backend("POSTGRES_USER", user)
    context.set_backend("POSTGRES_PASSWORD", password, mask=True)
    context.set_backend("POSTGRES_DB", db_name)

    derived = _build_local_postgres_url(
        username=user,
        password=password,
        host="localhost",
        port=port,
        database=db_name,
    )
    context.set_backend("DATABASE_URL", derived)


def _infer_local_db_mode(existing_url: str) -> str:
    if not existing_url:
        return "compose"
    try:
        parsed = urlparse(existing_url)
    except ValueError:
        return "compose"
    host = (parsed.hostname or "").strip().lower()
    if host and host not in {"localhost", "127.0.0.1"}:
        return "external"
    return "compose"


def _build_local_postgres_url(
    *,
    username: str,
    password: str,
    host: str,
    port: int,
    database: str,
) -> str:
    user_enc = quote(username, safe="")
    pass_enc = quote(password, safe="")
    db_enc = quote(database, safe="")
    return f"postgresql+asyncpg://{user_enc}:{pass_enc}@{host}:{port}/{db_enc}"


__all__ = ["collect_database"]
