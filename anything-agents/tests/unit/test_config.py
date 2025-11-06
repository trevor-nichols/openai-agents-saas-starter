"""Unit tests for application configuration settings."""

import pytest

from app.core.config import Settings


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
