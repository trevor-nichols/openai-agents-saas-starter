from datetime import UTC, datetime

from app.core.settings import Settings
from app.presentation.emails import (
    EmailTemplateContent,
    render_password_reset_email,
    render_verification_email,
)


def _settings() -> Settings:
    base = Settings()
    return base.model_copy(
        update={"app_name": "Agents", "app_public_url": "https://app.example.com"}
    )


def test_render_verification_email_uses_public_url() -> None:
    settings = _settings()
    expires = datetime(2025, 1, 1, 12, tzinfo=UTC)
    content = render_verification_email(settings, token="abc123", expires_at=expires)
    assert isinstance(content, EmailTemplateContent)
    assert "https://app.example.com/verify-email" in content.html
    assert "abc123" in content.text
    assert content.subject.startswith("Verify your email")


def test_render_password_reset_email_provides_cta() -> None:
    settings = _settings()
    expires = datetime(2025, 1, 1, 12, tzinfo=UTC)
    content = render_password_reset_email(settings, token="reset123", expires_at=expires)
    assert "https://app.example.com/reset-password" in content.html
    assert "reset123" in content.text
    assert content.action_url.endswith("token=reset123")
