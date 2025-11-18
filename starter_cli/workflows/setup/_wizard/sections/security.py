"""Security and rate-limit prompts for the setup wizard."""

from __future__ import annotations

import secrets
from collections.abc import Sequence

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIError

from ...inputs import HeadlessInputProvider, InputProvider
from ..context import WizardContext

_LOCKOUT_FIELDS: Sequence[tuple[str, str, int]] = (
    ("AUTH_IP_LOCKOUT_THRESHOLD", "Per-IP lockout threshold", 50),
    ("AUTH_IP_LOCKOUT_WINDOW_MINUTES", "Per-IP lockout window (minutes)", 10),
    ("AUTH_IP_LOCKOUT_DURATION_MINUTES", "Per-IP lockout duration (minutes)", 10),
    ("AUTH_LOCKOUT_THRESHOLD", "Per-user lockout threshold", 5),
    ("AUTH_LOCKOUT_WINDOW_MINUTES", "Per-user lockout window (minutes)", 60),
    ("AUTH_LOCKOUT_DURATION_MINUTES", "Per-user lockout duration (minutes)", 60),
    ("AUTH_PASSWORD_HISTORY_COUNT", "Password history count", 5),
    ("AUTH_REFRESH_TOKEN_TTL_MINUTES", "Refresh token lifetime (minutes)", 43200),
    ("ACCESS_TOKEN_EXPIRE_MINUTES", "Access token lifetime (minutes)", 30),
)

_EMAIL_RESET_FIELDS: Sequence[tuple[str, str, int]] = (
    ("EMAIL_VERIFICATION_TOKEN_TTL_MINUTES", "Email verification token TTL (minutes)", 60),
    (
        "EMAIL_VERIFICATION_EMAIL_RATE_LIMIT_PER_HOUR",
        "Verification emails per account (per hour)",
        3,
    ),
    (
        "EMAIL_VERIFICATION_IP_RATE_LIMIT_PER_HOUR",
        "Verification emails per IP (per hour)",
        10,
    ),
    (
        "PASSWORD_RESET_EMAIL_RATE_LIMIT_PER_HOUR",
        "Password reset emails per account (per hour)",
        5,
    ),
    (
        "PASSWORD_RESET_IP_RATE_LIMIT_PER_HOUR",
        "Password reset emails per IP (per hour)",
        20,
    ),
    ("PASSWORD_RESET_TOKEN_TTL_MINUTES", "Password reset token TTL (minutes)", 30),
)

_STATUS_FIELDS: Sequence[tuple[str, str, int]] = (
    (
        "STATUS_SUBSCRIPTION_EMAIL_RATE_LIMIT_PER_HOUR",
        "Status subscription emails per hour",
        5,
    ),
    (
        "STATUS_SUBSCRIPTION_IP_RATE_LIMIT_PER_HOUR",
        "Status subscription IP attempts per hour",
        20,
    ),
    ("STATUS_SUBSCRIPTION_TOKEN_TTL_MINUTES", "Status subscription token TTL (minutes)", 60),
    (
        "STATUS_SUBSCRIPTION_WEBHOOK_TIMEOUT_SECONDS",
        "Status subscription webhook timeout (seconds)",
        5,
    ),
)

_RATE_LIMIT_FIELDS: Sequence[tuple[str, str, int]] = (
    ("CHAT_RATE_LIMIT_PER_MINUTE", "Chat completions per minute", 60),
    ("CHAT_STREAM_RATE_LIMIT_PER_MINUTE", "Streaming chats per minute", 30),
    ("CHAT_STREAM_CONCURRENT_LIMIT", "Concurrent streaming chats", 5),
    (
        "BILLING_STREAM_RATE_LIMIT_PER_MINUTE",
        "Billing stream subscriptions per minute",
        20,
    ),
    ("BILLING_STREAM_CONCURRENT_LIMIT", "Concurrent billing streams", 3),
)

_DEFAULT_RATE_LIMIT_PREFIX = "rate-limit"
_DEFAULT_JWKS_CACHE_SECONDS = 300
_DEFAULT_JWKS_MAX_AGE_SECONDS = 300
_PLACEHOLDER_JWKS_SALT = "local-jwks-salt"


def run(context: WizardContext, provider: InputProvider) -> None:
    console.section(
        "Security & Rate Limits",
        "Dial in lockouts, token lifetimes, and email/reset policies before launch.",
    )
    _configure_auth_lockouts(context, provider)
    _configure_jwks_cache(context, provider)
    _configure_email_password_status(context, provider)
    _configure_rate_limits(context, provider)


def _configure_auth_lockouts(context: WizardContext, provider: InputProvider) -> None:
    for key, prompt, default in _LOCKOUT_FIELDS:
        _prompt_positive_int(context, provider, key=key, prompt=prompt, default=default)


def _configure_jwks_cache(context: WizardContext, provider: InputProvider) -> None:
    _prompt_positive_int(
        context,
        provider,
        key="AUTH_JWKS_CACHE_SECONDS",
        prompt="JWKS cache seconds",
        default=_DEFAULT_JWKS_CACHE_SECONDS,
    )
    _prompt_positive_int(
        context,
        provider,
        key="AUTH_JWKS_MAX_AGE_SECONDS",
        prompt="JWKS Cache-Control max-age (seconds)",
        default=_DEFAULT_JWKS_MAX_AGE_SECONDS,
    )
    current = context.current("AUTH_JWKS_ETAG_SALT")
    if current and current != _PLACEHOLDER_JWKS_SALT:
        context.set_backend("AUTH_JWKS_ETAG_SALT", current)
        return
    salt = provider.prompt_string(
        key="AUTH_JWKS_ETAG_SALT",
        prompt="JWKS ETag salt (leave blank to randomize)",
        default="",
        required=False,
    ).strip()
    if not salt:
        salt = secrets.token_urlsafe(16)
        console.info("Generated random JWKS ETag salt.", topic="wizard")
    context.set_backend("AUTH_JWKS_ETAG_SALT", salt)


def _configure_email_password_status(context: WizardContext, provider: InputProvider) -> None:
    for key, prompt, default in _EMAIL_RESET_FIELDS:
        _prompt_positive_int(context, provider, key=key, prompt=prompt, default=default)

    for key, prompt, default in _STATUS_FIELDS:
        _prompt_positive_int(context, provider, key=key, prompt=prompt, default=default)

    context.ensure_secret(
        provider,
        key="STATUS_SUBSCRIPTION_ENCRYPTION_KEY",
        label="Status subscription encryption key",
        length=64,
    )
    context.ensure_secret(
        provider,
        key="STATUS_SUBSCRIPTION_TOKEN_PEPPER",
        label="Status subscription token pepper",
        length=32,
    )


def _configure_rate_limits(context: WizardContext, provider: InputProvider) -> None:
    for key, prompt, default in _RATE_LIMIT_FIELDS:
        _prompt_positive_int(context, provider, key=key, prompt=prompt, default=default)

    prefix_default = context.current("RATE_LIMIT_KEY_PREFIX") or _DEFAULT_RATE_LIMIT_PREFIX
    prefix = provider.prompt_string(
        key="RATE_LIMIT_KEY_PREFIX",
        prompt="Redis key prefix for rate limiting",
        default=prefix_default,
        required=True,
    )
    context.set_backend("RATE_LIMIT_KEY_PREFIX", prefix)


def _prompt_positive_int(
    context: WizardContext,
    provider: InputProvider,
    *,
    key: str,
    prompt: str,
    default: int,
) -> int:
    default_str = context.current(key) or str(default)
    while True:
        raw_value = provider.prompt_string(
            key=key,
            prompt=prompt,
            default=default_str,
            required=True,
        ).strip()
        try:
            parsed = int(raw_value)
        except ValueError:
            if isinstance(provider, HeadlessInputProvider):
                raise CLIError(f"{key} must be an integer.") from None
            console.warn(f"{key} must be an integer.", topic="wizard")
            continue
        if parsed <= 0:
            if isinstance(provider, HeadlessInputProvider):
                raise CLIError(f"{key} must be greater than zero.")
            console.warn(f"{key} must be greater than zero.", topic="wizard")
            continue
        context.set_backend(key, str(parsed))
        return parsed
