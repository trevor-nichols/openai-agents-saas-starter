"""Hermetic platform smoke: health, JWKS, and agent registry check.

Run this in CI to ensure the FastAPI app boots with stubbed provider and
minimal env (SQLite + Redis service) without hitting external APIs.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from fastapi.testclient import TestClient
import importlib.util

# Ensure we import the repo-local api-service rather than any installed "app" package.
ROOT = Path(__file__).resolve().parents[2]
_original_sys_path = list(sys.path)
_stdlib_paths = [p for p in _original_sys_path if "python3.11" in p or "python311.zip" in p]
_site_packages = [p for p in _original_sys_path if "site-packages" in p]
sys.path = [
    str(ROOT / "apps" / "api-service" / "src"),
    str(ROOT / "apps" / "api-service"),
    str(ROOT / "packages" / "starter_contracts" / "src"),
    str(ROOT / "packages" / "starter_providers" / "src"),
    str(ROOT),
    *_stdlib_paths,
    *_site_packages,
]

app_pkg_init = ROOT / "apps" / "api-service" / "src" / "app" / "__init__.py"
spec = importlib.util.spec_from_file_location(
    "app",
    app_pkg_init,
    submodule_search_locations=[str(app_pkg_init.parent)],
)
if spec and spec.loader:
    app_module = importlib.util.module_from_spec(spec)
    sys.modules["app"] = app_module
    spec.loader.exec_module(app_module)
else:  # pragma: no cover - defensive
    raise RuntimeError("Failed to load local app package for smoke test")

# ---------------------------------------------------------------------------
# Environment defaults for a minimal, self-contained boot
# ---------------------------------------------------------------------------
os.environ["ENVIRONMENT"] = "test"
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("RATE_LIMIT_REDIS_URL", os.environ["REDIS_URL"])
os.environ.setdefault("AUTH_CACHE_REDIS_URL", os.environ["REDIS_URL"])
os.environ.setdefault("SECURITY_TOKEN_REDIS_URL", os.environ["REDIS_URL"])
os.environ.setdefault("USAGE_GUARDRAIL_REDIS_URL", os.environ["REDIS_URL"])
os.environ.setdefault("ENABLE_BILLING", "false")
os.environ.setdefault("ENABLE_BILLING_RETRY_WORKER", "false")
os.environ.setdefault("ENABLE_RESEND_EMAIL_DELIVERY", "false")
os.environ.setdefault("ALLOW_PUBLIC_SIGNUP", "true")
os.environ.setdefault("AUTO_RUN_MIGRATIONS", "false")
os.environ.setdefault("OPENAI_API_KEY", "dummy-smoke-key")
# Use deterministic test keyset for JWKS so smoke can validate /.well-known/jwks.json
TEST_KEYSET = ROOT / "apps" / "api-service" / "tests" / "fixtures" / "keysets" / "test_keyset.json"
os.environ.setdefault("AUTH_KEY_STORAGE_BACKEND", "file")
os.environ.setdefault("AUTH_KEY_STORAGE_PATH", str(TEST_KEYSET))
# Avoid CLI probes inside app bootstrap
os.environ.setdefault("STARTER_CONSOLE_SKIP_ENV", "true")
os.environ.setdefault("STARTER_CONSOLE_SKIP_VAULT_PROBE", "true")


# ---------------------------------------------------------------------------
# Stub agent provider to avoid external OpenAI calls during smoke
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class _StubDescriptor:
    key: str
    display_name: str
    description: str
    model: str
    capabilities: tuple[str, ...] = ()
    status: str = "active"


class _StubSessionStore:
    def build(self, session_id: str):
        return {"session_id": session_id}


class _StubRuntime:
    async def stream_chat(self, *args, **kwargs):  # pragma: no cover - not used in smoke
        class _Handle:
            async def aiter(self):
                if False:
                    yield None
        return _Handle()


class _StubProvider:
    name = "stub"

    def __init__(self) -> None:
        self._descriptor = _StubDescriptor(
            key="stub-agent",
            display_name="Stub Agent",
            description="Smoke-test stub agent",
            model="gpt-5.1",
        )
        self.runtime = _StubRuntime()
        self.session_store = _StubSessionStore()

    def list_agents(self) -> Sequence[_StubDescriptor]:
        return [self._descriptor]

    def resolve_agent(self, preferred_key: str | None = None) -> _StubDescriptor:
        return self._descriptor

    def get_agent(self, agent_key: str) -> _StubDescriptor | None:
        return self._descriptor if agent_key in {self._descriptor.key, self._descriptor.display_name} else None

    def default_agent_key(self) -> str:
        return self._descriptor.key

    def tool_overview(self) -> dict[str, Any]:
        return {self._descriptor.key: []}

    def mark_seen(self, agent_key: str, ts):  # pragma: no cover - smoke-only stub
        return None


# Monkeypatch the provider factory before app import so lifespan uses the stub.
main_spec = importlib.util.spec_from_file_location(
    "app.main",
    ROOT / "apps" / "api-service" / "src" / "main.py",
)
if not main_spec or not main_spec.loader:  # pragma: no cover - defensive
    raise RuntimeError("Failed to load app.main module for smoke test")
main = importlib.util.module_from_spec(main_spec)
sys.modules["app.main"] = main
main_spec.loader.exec_module(main)

# Monkeypatch before creating the application instance so lifespan uses the stub.
main.build_openai_provider = lambda **_: _StubProvider()  # type: ignore[attr-defined]


def _force_sqlite_json_compat() -> None:
    """SQLite lacks JSONB; for smoke with in-memory DB, downgrade to JSON."""
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url.startswith("sqlite"):
        return

    from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
    from app.infrastructure.persistence.models import base

    for table in base.Base.metadata.tables.values():
        for col in table.columns:
            if getattr(col.type, "__class__", type(None)).__name__ == "JSONB":
                col.type = SQLITE_JSON()


def main_smoke() -> None:
    from app.services.agents.provider_registry import get_provider_registry
    _force_sqlite_json_compat()
    app_instance = main.create_application()

    with TestClient(app_instance) as client:
        health = client.get("/health/ready")
        assert health.status_code == 200, health.text

        jwks = client.get("/.well-known/jwks.json")
        assert jwks.status_code == 200, jwks.text
        payload = jwks.json()
        assert payload.get("keys"), "JWKS keys missing"

        registry = get_provider_registry()
        provider = registry.get_default()
        agents = provider.list_agents()
        assert agents and agents[0].key == "stub-agent"

    print("platform smoke passed: health, jwks, stub agent registry")


if __name__ == "__main__":
    main_smoke()
