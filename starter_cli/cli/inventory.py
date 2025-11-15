from __future__ import annotations

"""Shared configuration metadata used across Starter CLI commands."""

from typing import Final

# Environment variables that the setup wizard currently prompts operators to
# populate. Keeping this list centralized allows the config commands and any
# reporting utilities to reason about coverage without duplicating literals.
WIZARD_PROMPTED_ENV_VARS: Final[frozenset[str]] = frozenset(
    {
        "ENVIRONMENT",
        "DEBUG",
        "PORT",
        "APP_PUBLIC_URL",
        "ALLOWED_HOSTS",
        "ALLOWED_ORIGINS",
        "AUTO_RUN_MIGRATIONS",
        "API_BASE_URL",
        "SECRET_KEY",
        "AUTH_PASSWORD_PEPPER",
        "AUTH_REFRESH_TOKEN_PEPPER",
        "AUTH_EMAIL_VERIFICATION_TOKEN_PEPPER",
        "AUTH_PASSWORD_RESET_TOKEN_PEPPER",
        "AUTH_SESSION_ENCRYPTION_KEY",
        "AUTH_SESSION_IP_HASH_SALT",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "XAI_API_KEY",
        "TAVILY_API_KEY",
        "REDIS_URL",
        "BILLING_EVENTS_REDIS_URL",
        "ENABLE_BILLING",
        "ENABLE_BILLING_STREAM",
        "ENABLE_BILLING_RETRY_WORKER",
        "ENABLE_BILLING_STREAM_REPLAY",
        "BILLING_RETRY_DEPLOYMENT_MODE",
        "STRIPE_SECRET_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "STRIPE_PRODUCT_PRICE_MAP",
        "RESEND_EMAIL_ENABLED",
        "RESEND_BASE_URL",
        "RESEND_API_KEY",
        "RESEND_DEFAULT_FROM",
        "RESEND_EMAIL_VERIFICATION_TEMPLATE_ID",
        "RESEND_PASSWORD_RESET_TEMPLATE_ID",
        "TENANT_DEFAULT_SLUG",
        "LOGGING_SINK",
        "LOGGING_DATADOG_API_KEY",
        "LOGGING_DATADOG_SITE",
        "LOGGING_OTLP_ENDPOINT",
        "LOGGING_OTLP_HEADERS",
        "GEOIP_PROVIDER",
        "GEOIP_MAXMIND_LICENSE_KEY",
        "GEOIP_IP2LOCATION_API_KEY",
        "ALLOW_PUBLIC_SIGNUP",
        "ALLOW_SIGNUP_TRIAL_OVERRIDE",
        "SIGNUP_RATE_LIMIT_PER_HOUR",
        "SIGNUP_DEFAULT_PLAN_CODE",
        "SIGNUP_DEFAULT_TRIAL_DAYS",
        "VAULT_VERIFY_ENABLED",
        "VAULT_ADDR",
        "VAULT_TOKEN",
        "VAULT_TRANSIT_KEY",
        "DATABASE_URL",
    }
)

# Frontend env vars that the wizard can populate for the Next.js app when the
# frontend workspace exists locally.
FRONTEND_ENV_VARS: Final[frozenset[str]] = frozenset(
    {
        "NEXT_PUBLIC_API_URL",
        "PLAYWRIGHT_BASE_URL",
        "AGENT_API_MOCK",
        "AGENT_FORCE_SECURE_COOKIES",
        "AGENT_ALLOW_INSECURE_COOKIES",
    }
)

__all__ = ["WIZARD_PROMPTED_ENV_VARS", "FRONTEND_ENV_VARS"]
