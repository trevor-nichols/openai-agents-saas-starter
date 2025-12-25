from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_APP_URL = "http://localhost:3000"


def parse_host_port(url: str, *, default_port: int) -> tuple[str, int]:
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or default_port
    return host, port


def is_local_host(host: str) -> bool:
    if host in {"localhost", "::1", "0.0.0.0"}:
        return True
    # IPv4 loopback range (RFC 1122) is 127.0.0.0/8, not just 127.0.0.1.
    if host.startswith("127."):
        return True
    return host.endswith(".local")


def api_base_url(env: Mapping[str, str]) -> str:
    return env.get("API_BASE_URL") or DEFAULT_API_URL


def app_public_url(env: Mapping[str, str]) -> str:
    return env.get("APP_PUBLIC_URL") or DEFAULT_APP_URL


def frontend_listen_port(env: Mapping[str, str]) -> int:
    host, url_port = parse_host_port(app_public_url(env), default_port=3000)
    if is_local_host(host):
        return url_port

    env_port = env.get("PORT")
    if env_port and env_port.isdigit():
        return int(env_port)

    return 3000


def build_backend_env(
    env: Mapping[str, str],
    *,
    project_root: Path,
    base_log_root: Path,
) -> dict[str, str]:
    merged = dict(env)
    merged.pop("PORT", None)  # avoid inheriting frontend port for uvicorn
    merged["LOG_ROOT"] = str(base_log_root)
    merged.setdefault(
        "ALEMBIC_CONFIG",
        str(project_root / "apps" / "api-service" / "alembic.ini"),
    )
    merged.setdefault(
        "ALEMBIC_SCRIPT_LOCATION",
        str(project_root / "apps" / "api-service" / "alembic"),
    )
    return merged


def build_frontend_env(
    env: Mapping[str, str],
    *,
    base_log_root: Path,
) -> dict[str, str]:
    merged = dict(env)
    merged["PORT"] = str(frontend_listen_port(merged))
    merged.setdefault("APP_PUBLIC_URL", DEFAULT_APP_URL)
    merged["LOG_ROOT"] = str(base_log_root)
    return merged


__all__ = [
    "DEFAULT_API_URL",
    "DEFAULT_APP_URL",
    "api_base_url",
    "app_public_url",
    "build_backend_env",
    "build_frontend_env",
    "frontend_listen_port",
    "is_local_host",
    "parse_host_port",
]
