"""Unit tests for application configuration settings."""

import pytest

from app.core.config import Settings


def sanitized_settings(**overrides) -> Settings:
    """Return a Settings copy with deterministic, test-friendly values."""

    base = Settings()
    defaults = {
        "stripe_secret_key": None,
        "stripe_webhook_secret": None,
        "stripe_product_price_map": {},
        "enable_billing_stream": False,
        "billing_events_redis_url": None,
    }
    defaults.update(overrides)
    return base.model_copy(update=defaults)


def test_auth_audience_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify default JWT audience list is applied when no override is provided."""

    monkeypatch.delenv("AUTH_AUDIENCE", raising=False)

    settings = Settings()

    assert settings.auth_audience == [
        "agent-api",
        "analytics-service",
        "billing-worker",
        "support-console",
        "synthetic-monitor",
    ]


def test_auth_audience_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure JSON array environment variables are parsed correctly."""

    monkeypatch.setenv(
        "AUTH_AUDIENCE",
        '["foo-service", "bar-service", "baz-service"]',
    )

    settings = Settings()

    assert settings.auth_audience == ["foo-service", "bar-service", "baz-service"]


@pytest.mark.parametrize("bad_value", [123, "", [], ["   "]])
def test_auth_audience_validation_errors(bad_value: object) -> None:
    """Invalid audience configuration raises a validation error."""

    with pytest.raises(ValueError):
        Settings(auth_audience=bad_value)  # type: ignore[arg-type]


def test_required_stripe_envs_missing_detects_blanks() -> None:
    """Missing Stripe variables are reported for billing guardrails."""

    settings = sanitized_settings(
        stripe_secret_key="   ",
        stripe_webhook_secret=None,
        stripe_product_price_map={},
    )

    assert settings.required_stripe_envs_missing() == [
        "STRIPE_SECRET_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "STRIPE_PRODUCT_PRICE_MAP",
    ]


def test_required_stripe_envs_missing_returns_empty_when_configured() -> None:
    """Guardrail helper returns an empty list when all values exist."""

    settings = sanitized_settings(
        stripe_secret_key="sk_test_1234567890",
        stripe_webhook_secret="whsec_abcdef123456",
        stripe_product_price_map={"starter": "price_123"},
    )

    assert settings.required_stripe_envs_missing() == []


def test_stripe_configuration_summary_masks_tokens() -> None:
    """Masked summary hides sensitive data while exposing plan context."""

    settings = sanitized_settings(
        stripe_secret_key="sk_test_1234567890",
        stripe_webhook_secret="whsec_abcd987654321",
        stripe_product_price_map={"starter": "price_123", "pro": "price_456"},
        enable_billing_stream=True,
        billing_events_redis_url="redis://billing-events:6379/1",
    )

    summary = settings.stripe_configuration_summary()

    secret_mask = summary["stripe_secret_key"]
    webhook_mask = summary["stripe_webhook_secret"]

    assert secret_mask.startswith("sk") and secret_mask.endswith("7890")
    assert all(char == "*" for char in secret_mask[2:-4])
    assert webhook_mask.endswith("4321")
    assert summary["plan_count"] == 2
    assert summary["plans_configured"] == ["pro", "starter"]
    assert summary["billing_stream_enabled"] is True
    assert summary["billing_stream_backend"] == "BILLING_EVENTS_REDIS_URL"
