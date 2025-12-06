"""Configuration loader for HTTP smoke tests.

These tests run against a live api-service instance (often localhost). Values
come from env vars so CI and local dev can point at different hosts without
changing test code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class SmokeConfig:
    base_url: str
    tenant_slug: str
    tenant_name: str
    admin_email: str
    admin_password: str
    fixture_conversation_key: str
    request_timeout: float
    enable_billing: bool
    enable_ai: bool
    enable_vector: bool
    enable_containers: bool


def load_config() -> SmokeConfig:
    return SmokeConfig(
        base_url=os.getenv("SMOKE_BASE_URL", "http://localhost:8000"),
        tenant_slug=os.getenv("SMOKE_TENANT_SLUG", "smoke"),
        tenant_name=os.getenv("SMOKE_TENANT_NAME", "Smoke Test Tenant"),
        admin_email=os.getenv("SMOKE_USER_EMAIL", "smoke-admin@example.com"),
        admin_password=os.getenv("SMOKE_USER_PASSWORD", "SmokeAdmin!234"),
        fixture_conversation_key=os.getenv("SMOKE_CONVERSATION_KEY", "seeded-smoke-convo"),
        request_timeout=float(os.getenv("SMOKE_HTTP_TIMEOUT", "10")),
        enable_billing=_env_bool("SMOKE_ENABLE_BILLING", False),
        enable_ai=_env_bool("SMOKE_ENABLE_AI", False),
        enable_vector=_env_bool("SMOKE_ENABLE_VECTOR", False),
        enable_containers=_env_bool("SMOKE_ENABLE_CONTAINERS", False),
    )


__all__ = ["SmokeConfig", "load_config"]
