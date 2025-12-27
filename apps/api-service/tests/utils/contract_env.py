from __future__ import annotations

import os

TEST_TENANT_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_SCOPE = "conversations:read conversations:write conversations:delete tools:read"


def configure_contract_env(*, enable_billing: bool = False) -> None:
    """Set deterministic env defaults for contract-level API tests."""

    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
    os.environ.setdefault("RATE_LIMIT_REDIS_URL", os.environ["REDIS_URL"])
    os.environ.setdefault("AUTH_CACHE_REDIS_URL", os.environ["REDIS_URL"])
    os.environ.setdefault("SECURITY_TOKEN_REDIS_URL", os.environ["REDIS_URL"])
    os.environ.setdefault("USAGE_GUARDRAIL_REDIS_URL", os.environ["REDIS_URL"])
    os.environ.setdefault("ENABLE_USAGE_GUARDRAILS", "false")

    if enable_billing:
        os.environ["ENABLE_BILLING"] = "true"
        os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_contract")
        os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_contract")
        os.environ.setdefault("STRIPE_PRODUCT_PRICE_MAP", "starter=price_contract")
    else:
        os.environ.setdefault("ENABLE_BILLING", "false")
