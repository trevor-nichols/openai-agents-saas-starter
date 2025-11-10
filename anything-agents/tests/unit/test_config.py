"""Unit tests for application configuration settings."""

import pytest

from app.core.config import Settings


def make_settings(**overrides) -> Settings:
    """Instantiate Settings without loading repo env files."""

    return Settings(_env_file=None, **overrides)


def sanitized_settings(**overrides) -> Settings:
    """Return a Settings copy with deterministic, test-friendly values."""

    base = make_settings()
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

    settings = make_settings()

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

    settings = make_settings()

    assert settings.auth_audience == ["foo-service", "bar-service", "baz-service"]


@pytest.mark.parametrize("bad_value", [123, "", [], ["   "]])
def test_auth_audience_validation_errors(bad_value: object) -> None:
    """Invalid audience configuration raises a validation error."""

    with pytest.raises(ValueError):
        make_settings(auth_audience=bad_value)  # type: ignore[arg-type]


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
    plan_count = summary["plan_count"]
    plans_configured = summary["plans_configured"]
    billing_enabled = summary["billing_stream_enabled"]
    backend = summary["billing_stream_backend"]

    assert isinstance(secret_mask, str)
    assert isinstance(webhook_mask, str)
    assert isinstance(plan_count, int)
    assert isinstance(plans_configured, list)
    assert all(isinstance(plan, str) for plan in plans_configured)
    assert isinstance(billing_enabled, bool)
    assert isinstance(backend, str | type(None))

    assert secret_mask.startswith("sk") and secret_mask.endswith("7890")
    assert all(char == "*" for char in secret_mask[2:-4])
    assert webhook_mask.endswith("4321")
    assert plan_count == 2
    assert plans_configured == ["pro", "starter"]
    assert billing_enabled is True
    assert backend == "BILLING_EVENTS_REDIS_URL"


def test_signup_settings_defaults() -> None:
    """Public signup toggles expose sensible defaults for starter deployments."""

    settings = make_settings()

    assert settings.allow_public_signup is True
    assert settings.signup_rate_limit_per_hour == 20
    assert settings.signup_default_plan_code == "starter"
    assert settings.signup_default_trial_days == 14


def test_signup_rate_limit_requires_positive_values() -> None:
    """Negative signup rate limits are rejected."""

    with pytest.raises(ValueError):
        make_settings(signup_rate_limit_per_hour=-5)


def test_allowed_hosts_default_includes_local_and_test_hosts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Baseline trusted hosts cover localhost and FastAPI test clients."""

    monkeypatch.delenv("ALLOWED_HOSTS", raising=False)

    settings = make_settings()

    hosts = settings.get_allowed_hosts_list()

    assert {"localhost", "localhost:8000", "127.0.0.1"}.issubset(set(hosts))
    assert "testserver" in hosts
    assert "testclient" in hosts


def test_allowed_hosts_env_override_respects_production_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Explicit ALLOWED_HOSTS override is honored without adding test-only hosts."""

    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("ALLOWED_HOSTS", "api.example.com,docs.example.com")
    monkeypatch.setenv("DEBUG", "false")

    settings = make_settings()

    hosts = settings.get_allowed_hosts_list()

    assert hosts == ["api.example.com", "docs.example.com"]


def test_allowed_origins_default_matches_frontend_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The default CORS list aligns with local frontend + API ports."""

    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)

    settings = make_settings()

    assert settings.get_allowed_origins_list() == [
        "http://localhost:3000",
        "http://localhost:8000",
    ]
