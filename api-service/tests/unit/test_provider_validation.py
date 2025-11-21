"""Unit tests for provider validation helpers."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.core.provider_validation import ensure_provider_parity, validate_providers


def test_validate_providers_returns_empty_when_features_disabled():
    settings = Settings()

    violations = validate_providers(settings, strict=True)

    assert violations == []


def test_validate_providers_flags_stripe_when_billing_enabled():
    settings = Settings()
    settings.enable_billing = True
    settings.stripe_secret_key = None
    settings.stripe_webhook_secret = None
    settings.stripe_product_price_map = {}

    violations = validate_providers(settings, strict=True)

    assert {v.code for v in violations} == {
        "missing_stripe_secret_key",
        "missing_stripe_webhook_secret",
        "missing_stripe_product_price_map",
    }
    assert all(v.provider == "stripe" for v in violations)
    assert all(v.fatal for v in violations)


def test_validate_providers_handles_resend_in_non_strict_environment():
    settings = Settings()
    settings.environment = "development"
    settings.enable_resend_email_delivery = True
    settings.resend_api_key = None
    settings.resend_default_from = None

    violations = validate_providers(settings, strict=False)

    assert len(violations) == 2
    assert {v.code for v in violations} == {
        "missing_resend_api_key",
        "missing_resend_default_from",
    }
    assert all(not v.fatal for v in violations)


def test_validate_providers_flags_tavily_when_missing_key():
    settings = Settings()
    settings.tavily_api_key = None

    violations = validate_providers(settings, strict=True)

    assert len(violations) == 1
    violation = violations[0]
    assert violation.provider == "tavily"
    assert violation.fatal is False


def test_ensure_provider_parity_raises_when_fatal_violations_present():
    settings = Settings()
    settings.enable_billing = True
    settings.stripe_secret_key = None
    settings.stripe_webhook_secret = None
    settings.stripe_product_price_map = {}
    violations = validate_providers(settings, strict=True)

    with pytest.raises(RuntimeError):
        ensure_provider_parity(settings, violations=violations)
@pytest.fixture(autouse=True)
def _clear_provider_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove provider-related env vars so tests control state explicitly."""

    for key in (
        "ENABLE_BILLING",
        "RESEND_EMAIL_ENABLED",
        "STRIPE_SECRET_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "STRIPE_PRODUCT_PRICE_MAP",
        "RESEND_API_KEY",
        "RESEND_DEFAULT_FROM",
        "TAVILY_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)
