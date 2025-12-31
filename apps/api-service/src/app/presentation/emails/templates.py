"""Local HTML/text templates for auth-related emails."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from textwrap import dedent
from urllib.parse import urlencode

from app.core.settings import Settings


@dataclass(slots=True)
class EmailTemplateContent:
    subject: str
    html: str
    text: str
    action_url: str


def render_verification_email(
    settings: Settings,
    token: str,
    expires_at: datetime,
) -> EmailTemplateContent:
    base_url = _normalized_base_url(settings)
    verification_url = f"{base_url}/verify-email?{urlencode({'token': token})}"
    subject = f"Verify your email for {settings.app_name}"
    expires_str = _format_timestamp(expires_at)
    html = _wrap_html(
        heading="Confirm your email",
        body=(
            f"You're almost done setting up <strong>{settings.app_name}</strong>. "
            "Click the button below or enter the code to finish verifying your email address."
        ),
        cta_label="Verify email",
        cta_url=verification_url,
        footer=f"This link expires {expires_str}.",
        code=token,
    )
    text = _plain_text_message(
        intro=f"You're almost done setting up {settings.app_name}.",
        instructions="Use the link or code below to verify your email.",
        action_url=verification_url,
        code=token,
        expires=expires_str,
    )
    return EmailTemplateContent(subject=subject, html=html, text=text, action_url=verification_url)


def render_password_reset_email(
    settings: Settings,
    token: str,
    expires_at: datetime,
) -> EmailTemplateContent:
    base_url = _normalized_base_url(settings)
    reset_url = f"{base_url}/reset-password?{urlencode({'token': token})}"
    subject = f"Reset your {settings.app_name} password"
    expires_str = _format_timestamp(expires_at)
    html = _wrap_html(
        heading="Reset your password",
        body=(
            f"We received a request to reset your <strong>{settings.app_name}</strong> password. "
            "If this was you, click the button below or enter the code to continue."
        ),
        cta_label="Reset password",
        cta_url=reset_url,
        footer=f"This link expires {expires_str}.",
        code=token,
    )
    text = _plain_text_message(
        intro=f"We received a request to reset your {settings.app_name} password.",
        instructions="Use the link or code below to choose a new password.",
        action_url=reset_url,
        code=token,
        expires=expires_str,
    )
    return EmailTemplateContent(subject=subject, html=html, text=text, action_url=reset_url)


def render_team_invite_email(
    settings: Settings,
    *,
    token: str,
    tenant_name: str,
    role: str,
    expires_at: datetime | None,
) -> EmailTemplateContent:
    base_url = _normalized_base_url(settings)
    accept_url = f"{base_url}/accept-invite?{urlencode({'token': token})}"
    subject = f"You're invited to join {tenant_name}"
    role_label = role.replace("_", " ").title()
    expires_str = _format_timestamp(expires_at) if expires_at else "This invite does not expire."
    html = _wrap_html(
        heading=f"Join {tenant_name}",
        body=(
            f"You've been invited to join <strong>{tenant_name}</strong> as a "
            f"<strong>{role_label}</strong>. Click the button below to accept your invite."
        ),
        cta_label="Accept invite",
        cta_url=accept_url,
        footer=expires_str,
        code=token,
    )
    text = _plain_text_message(
        intro=f"You've been invited to join {tenant_name} as a {role_label}.",
        instructions="Use the link or code below to accept your invite.",
        action_url=accept_url,
        code=token,
        expires=expires_str,
    )
    return EmailTemplateContent(subject=subject, html=html, text=text, action_url=accept_url)


def _normalized_base_url(settings: Settings) -> str:
    raw = (settings.app_public_url or "http://localhost:3000").strip()
    if not raw:
        raw = "http://localhost:3000"
    return raw.rstrip("/")


def _format_timestamp(timestamp: datetime) -> str:
    if timestamp.tzinfo is None:
        aware = timestamp.replace(tzinfo=UTC)
    else:
        aware = timestamp.astimezone(UTC)
    return aware.strftime("%B %d, %Y %H:%M %Z")


def _wrap_html(
    *,
    heading: str,
    body: str,
    cta_label: str,
    cta_url: str,
    footer: str,
    code: str,
) -> str:
    return dedent(
        f"""
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
          style="font-family:Arial,sans-serif;background-color:#f7f8fa;padding:24px;">
          <tr>
            <td align="center">
              <table role="presentation" width="600" cellpadding="0" cellspacing="0"
                style="background-color:#ffffff;border-radius:12px;padding:32px;text-align:left;color:#111827;">
                <tr>
                  <td style="font-size:22px;font-weight:600;">{heading}</td>
                </tr>
                <tr>
                  <td style="padding-top:16px;font-size:16px;line-height:1.5;">{body}</td>
                </tr>
                <tr>
                  <td style="padding:24px 0;">
                    <a href="{cta_url}"
                      style="display:inline-block;background-color:#111827;color:#ffffff;text-decoration:none;">
                      <span style="display:inline-block;padding:12px 24px;border-radius:8px;
                        font-weight:600;">
                        {cta_label}
                      </span>
                    </a>
                  </td>
                </tr>
                <tr>
                  <td style="font-size:16px;color:#111827;">Or use this code:</td>
                </tr>
                <tr>
                  <td style="font-size:24px;font-weight:700;letter-spacing:3px;padding:8px 0;">
                    {code}
                  </td>
                </tr>
                <tr>
                  <td style="font-size:14px;color:#6b7280;padding-top:16px;">{footer}</td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
        """
    ).strip()


def _plain_text_message(
    *,
    intro: str,
    instructions: str,
    action_url: str,
    code: str,
    expires: str,
) -> str:
    return (
        f"{intro}\n\n"
        f"{instructions}\n"
        f"Link: {action_url}\n"
        f"Code: {code}\n"
        f"Expires: {expires}\n\n"
        "If you did not request this, you can safely ignore this message."
    )


__all__ = [
    "EmailTemplateContent",
    "render_password_reset_email",
    "render_team_invite_email",
    "render_verification_email",
]
