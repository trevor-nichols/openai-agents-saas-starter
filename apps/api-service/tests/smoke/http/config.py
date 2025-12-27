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
    operator_email: str
    unverified_email: str
    mfa_email: str
    password_reset_email: str
    password_change_email: str
    fixture_conversation_key: str
    request_timeout: float
    enable_billing: bool
    enable_billing_stream: bool
    enable_ai: bool
    enable_activity_stream: bool
    enable_auth_signup: bool
    enable_auth_extended: bool
    enable_auth_mfa: bool
    enable_service_accounts: bool
    enable_contact: bool
    enable_status_subscriptions: bool
    enable_openai_files: bool
    openai_file_id: str | None
    enable_assets: bool
    enable_vector: bool
    enable_containers: bool


def load_config() -> SmokeConfig:
    return SmokeConfig(
        base_url=os.getenv("SMOKE_BASE_URL", "http://localhost:8000"),
        tenant_slug=os.getenv("SMOKE_TENANT_SLUG", "smoke"),
        tenant_name=os.getenv("SMOKE_TENANT_NAME", "Smoke Test Tenant"),
        admin_email=os.getenv("SMOKE_USER_EMAIL", "smoke-admin@example.com"),
        admin_password=os.getenv("SMOKE_USER_PASSWORD", "SmokeAdmin!234"),
        operator_email=os.getenv("SMOKE_OPERATOR_EMAIL", "smoke-operator@example.com"),
        unverified_email=os.getenv("SMOKE_UNVERIFIED_EMAIL", "smoke-unverified@example.com"),
        mfa_email=os.getenv("SMOKE_MFA_EMAIL", "smoke-mfa@example.com"),
        password_reset_email=os.getenv(
            "SMOKE_PASSWORD_RESET_EMAIL", "smoke-password-reset@example.com"
        ),
        password_change_email=os.getenv(
            "SMOKE_PASSWORD_CHANGE_EMAIL", "smoke-password-change@example.com"
        ),
        fixture_conversation_key=os.getenv("SMOKE_CONVERSATION_KEY", "seeded-smoke-convo"),
        request_timeout=float(os.getenv("SMOKE_HTTP_TIMEOUT", "10")),
        enable_billing=_env_bool("SMOKE_ENABLE_BILLING", False),
        enable_billing_stream=_env_bool("SMOKE_ENABLE_BILLING_STREAM", False),
        enable_ai=_env_bool("SMOKE_ENABLE_AI", False),
        enable_activity_stream=_env_bool("SMOKE_ENABLE_ACTIVITY_STREAM", False),
        enable_auth_signup=_env_bool("SMOKE_ENABLE_AUTH_SIGNUP", False),
        enable_auth_extended=_env_bool("SMOKE_ENABLE_AUTH_EXTENDED", False),
        enable_auth_mfa=_env_bool("SMOKE_ENABLE_AUTH_MFA", False),
        enable_service_accounts=_env_bool("SMOKE_ENABLE_SERVICE_ACCOUNTS", False),
        enable_contact=_env_bool("SMOKE_ENABLE_CONTACT", False),
        enable_status_subscriptions=_env_bool("SMOKE_ENABLE_STATUS_SUBSCRIPTIONS", False),
        enable_openai_files=_env_bool("SMOKE_ENABLE_OPENAI_FILES", False),
        openai_file_id=os.getenv("SMOKE_OPENAI_FILE_ID"),
        enable_assets=_env_bool("SMOKE_ENABLE_ASSETS", False),
        enable_vector=_env_bool("SMOKE_ENABLE_VECTOR", False),
        enable_containers=_env_bool("SMOKE_ENABLE_CONTAINERS", False),
    )


__all__ = ["SmokeConfig", "load_config"]
