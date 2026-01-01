"""Authentication, authorization, and token hygiene settings."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.core.paths import resolve_repo_path
from app.domain.secrets import SecretsProviderLiteral

from .base import SAFE_ENVIRONMENTS, BaseAppSettings

DEFAULT_SECRET_KEY = "your-secret-key-here-change-in-production"
DEFAULT_PASSWORD_PEPPER = "local-dev-password-pepper"
DEFAULT_PASSWORD_RESET_TOKEN_PEPPER = "local-reset-token-pepper"
DEFAULT_EMAIL_VERIFICATION_TOKEN_PEPPER = "local-email-verify-pepper"
DEFAULT_REFRESH_TOKEN_PEPPER = "local-dev-refresh-pepper"
DEFAULT_KEY_STORAGE_PATH = "var/keys/keyset.json"
PLACEHOLDER_SECRET_KEY = "change-me"
PLACEHOLDER_PASSWORD_PEPPER = "change-me-too"
PLACEHOLDER_REFRESH_TOKEN_PEPPER = "change-me-again"


class SecuritySettingsMixin(BaseModel):
    secret_key: str = Field(default=DEFAULT_SECRET_KEY, description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration time in minutes"
    )
    auth_audience: list[str] = Field(
        default_factory=lambda: [
            "agent-api",
            "analytics-service",
            "billing-worker",
            "support-console",
            "synthetic-monitor",
        ],
        description=(
            "Ordered list of permitted JWT audiences. Provide as JSON array via AUTH_AUDIENCE or "
            "comma-separated strings."
        ),
    )
    auth_key_storage_backend: str = Field(
        default="file",
        description="Key storage backend (file or secret-manager).",
        alias="AUTH_KEY_STORAGE_BACKEND",
    )
    auth_key_storage_provider: SecretsProviderLiteral | None = Field(
        default=None,
        description=(
            "Secrets provider used for Ed25519 keyset storage when "
            "auth_key_storage_backend=secret-manager."
        ),
        alias="AUTH_KEY_STORAGE_PROVIDER",
    )
    auth_key_storage_path: str = Field(
        default=DEFAULT_KEY_STORAGE_PATH,
        description="Filesystem path for keyset JSON when using file backend.",
        alias="AUTH_KEY_STORAGE_PATH",
    )
    auth_key_secret_name: str | None = Field(
        default=None,
        description="Secret-manager key/path storing keyset JSON when backend=secret-manager.",
        alias="AUTH_KEY_SECRET_NAME",
    )
    auth_jwks_cache_seconds: int = Field(
        default=300,
        description="Cache max-age for /.well-known/jwks.json responses.",
        alias="AUTH_JWKS_CACHE_SECONDS",
    )
    auth_jwks_max_age_seconds: int = Field(
        default=300,
        description="Preferred Cache-Control max-age for JWKS responses.",
        alias="AUTH_JWKS_MAX_AGE_SECONDS",
    )
    auth_jwks_etag_salt: str = Field(
        default="local-jwks-salt",
        description="Salt mixed into JWKS ETag derivation to avoid predictable hashes.",
        alias="AUTH_JWKS_ETAG_SALT",
    )
    auth_refresh_token_pepper: str = Field(
        default=DEFAULT_REFRESH_TOKEN_PEPPER,
        description="Server-side pepper prepended when hashing refresh tokens.",
        alias="AUTH_REFRESH_TOKEN_PEPPER",
    )
    auth_password_pepper: str = Field(
        default=DEFAULT_PASSWORD_PEPPER,
        description="Pepper prepended to human passwords prior to hashing.",
        alias="AUTH_PASSWORD_PEPPER",
    )
    auth_refresh_token_ttl_minutes: int = Field(
        default=43200,
        description="Default refresh token lifetime for human users (minutes).",
        alias="AUTH_REFRESH_TOKEN_TTL_MINUTES",
    )
    auth_session_encryption_key: str | None = Field(
        default=None,
        description=(
            "Base64-compatible secret used to encrypt stored IP metadata for user sessions."
        ),
        alias="AUTH_SESSION_ENCRYPTION_KEY",
    )
    auth_session_ip_hash_salt: str | None = Field(
        default=None,
        description="Salt blended into session IP hash derivation (defaults to SECRET_KEY).",
        alias="AUTH_SESSION_IP_HASH_SALT",
    )
    auth_password_history_count: int = Field(
        default=5,
        description="Number of historical password hashes retained per user.",
        alias="AUTH_PASSWORD_HISTORY_COUNT",
    )
    require_email_verification: bool = Field(
        default=True,
        description="Require verified email before accessing protected APIs.",
        alias="REQUIRE_EMAIL_VERIFICATION",
    )
    auth_email_verification_token_pepper: str = Field(
        default=DEFAULT_EMAIL_VERIFICATION_TOKEN_PEPPER,
        description="Pepper used when hashing email verification token secrets.",
        alias="AUTH_EMAIL_VERIFICATION_TOKEN_PEPPER",
    )
    auth_password_reset_token_pepper: str = Field(
        default=DEFAULT_PASSWORD_RESET_TOKEN_PEPPER,
        description="Pepper used to hash password reset token secrets.",
        alias="AUTH_PASSWORD_RESET_TOKEN_PEPPER",
    )
    password_reset_token_ttl_minutes: int = Field(
        default=30,
        description="Password reset token lifetime in minutes.",
        alias="PASSWORD_RESET_TOKEN_TTL_MINUTES",
    )
    password_reset_email_rate_limit_per_hour: int = Field(
        default=5,
        description="Password reset requests allowed per email per hour.",
        alias="PASSWORD_RESET_EMAIL_RATE_LIMIT_PER_HOUR",
    )
    password_reset_ip_rate_limit_per_hour: int = Field(
        default=20,
        description="Password reset requests allowed per IP per hour.",
        alias="PASSWORD_RESET_IP_RATE_LIMIT_PER_HOUR",
    )
    email_verification_token_ttl_minutes: int = Field(
        default=60,
        description="Email verification token lifetime in minutes.",
        alias="EMAIL_VERIFICATION_TOKEN_TTL_MINUTES",
    )
    email_verification_email_rate_limit_per_hour: int = Field(
        default=3,
        description="Verification email sends per account per hour.",
        alias="EMAIL_VERIFICATION_EMAIL_RATE_LIMIT_PER_HOUR",
    )
    email_verification_ip_rate_limit_per_hour: int = Field(
        default=10,
        description="Verification email sends per IP per hour.",
        alias="EMAIL_VERIFICATION_IP_RATE_LIMIT_PER_HOUR",
    )
    mfa_challenge_ttl_minutes: int = Field(
        default=5,
        description="Lifetime of MFA challenge tokens issued during login.",
        alias="MFA_CHALLENGE_TTL_MINUTES",
    )
    mfa_verify_rate_limit_per_hour: int = Field(
        default=10,
        description="Maximum MFA verification attempts per user per hour.",
        alias="MFA_VERIFY_RATE_LIMIT_PER_HOUR",
    )
    sso_start_rate_limit_per_minute: int = Field(
        default=30,
        description="SSO start requests allowed per minute.",
        alias="SSO_START_RATE_LIMIT_PER_MINUTE",
    )
    sso_callback_rate_limit_per_minute: int = Field(
        default=30,
        description="SSO callback requests allowed per minute.",
        alias="SSO_CALLBACK_RATE_LIMIT_PER_MINUTE",
    )
    contact_email_recipients: list[str] = Field(
        default_factory=lambda: ["support@localhost"],
        description=(
            "Comma-separated or JSON list of recipients for contact form submissions "
            "(e.g., support@example.com,security@example.com)."
        ),
        alias="CONTACT_EMAIL_TO",
    )
    contact_email_template_id: str | None = Field(
        default=None,
        description="Optional Resend template ID for contact form deliveries.",
        alias="CONTACT_EMAIL_TEMPLATE_ID",
    )
    contact_email_subject_prefix: str = Field(
        default="[Contact]",
        description="Subject prefix prepended to contact form emails.",
        alias="CONTACT_EMAIL_SUBJECT_PREFIX",
    )
    contact_email_rate_limit_per_email_per_hour: int = Field(
        default=3,
        description="Contact form submissions allowed per email per hour.",
        alias="CONTACT_EMAIL_EMAIL_RATE_LIMIT_PER_HOUR",
    )
    contact_email_rate_limit_per_ip_per_hour: int = Field(
        default=20,
        description="Contact form submissions allowed per IP per hour.",
        alias="CONTACT_EMAIL_IP_RATE_LIMIT_PER_HOUR",
    )
    enable_resend_email_delivery: bool = Field(
        default=False,
        description="When true, use Resend for transactional email delivery.",
        alias="RESEND_EMAIL_ENABLED",
    )
    resend_api_key: str | None = Field(
        default=None,
        description="Resend API key (re_...). Required when RESEND_EMAIL_ENABLED=true.",
        alias="RESEND_API_KEY",
    )
    resend_base_url: str = Field(
        default="https://api.resend.com",
        description="Override Resend API base URL for testing/sandbox environments.",
        alias="RESEND_BASE_URL",
    )
    resend_default_from: str | None = Field(
        default=None,
        description="Fully-qualified From address verified in Resend.",
        alias="RESEND_DEFAULT_FROM",
    )
    resend_email_verification_template_id: str | None = Field(
        default=None,
        description="Optional Resend template ID for email verification messages.",
        alias="RESEND_EMAIL_VERIFICATION_TEMPLATE_ID",
    )
    resend_password_reset_template_id: str | None = Field(
        default=None,
        description="Optional Resend template ID for password reset messages.",
        alias="RESEND_PASSWORD_RESET_TEMPLATE_ID",
    )
    status_subscription_token_ttl_minutes: int = Field(
        default=60,
        description="Status subscription email verification token lifetime in minutes.",
        alias="STATUS_SUBSCRIPTION_TOKEN_TTL_MINUTES",
    )
    status_subscription_email_rate_limit_per_hour: int = Field(
        default=5,
        description="Email subscription attempts per IP per hour.",
        alias="STATUS_SUBSCRIPTION_EMAIL_RATE_LIMIT_PER_HOUR",
    )
    status_subscription_ip_rate_limit_per_hour: int = Field(
        default=20,
        description="Webhook subscription attempts per IP per hour.",
        alias="STATUS_SUBSCRIPTION_IP_RATE_LIMIT_PER_HOUR",
    )
    status_subscription_token_pepper: str = Field(
        default="status-subscription-token-pepper",
        description="Pepper used to hash status subscription verification tokens.",
        alias="STATUS_SUBSCRIPTION_TOKEN_PEPPER",
    )
    status_subscription_encryption_key: str | None = Field(
        default=None,
        description="Override secret used to encrypt subscription targets and webhook secrets.",
        alias="STATUS_SUBSCRIPTION_ENCRYPTION_KEY",
    )
    status_subscription_webhook_timeout_seconds: int = Field(
        default=5,
        description="HTTP timeout applied when delivering webhook challenges (seconds).",
        alias="STATUS_SUBSCRIPTION_WEBHOOK_TIMEOUT_SECONDS",
    )
    auth_lockout_threshold: int = Field(
        default=5,
        description="Failed login attempts allowed before locking the account.",
        alias="AUTH_LOCKOUT_THRESHOLD",
    )
    auth_lockout_window_minutes: float = Field(
        default=60.0,
        description="Rolling window in minutes for lockout threshold calculations.",
        alias="AUTH_LOCKOUT_WINDOW_MINUTES",
    )
    auth_lockout_duration_minutes: float = Field(
        default=60.0,
        description="Automatic unlock window for locked users (minutes).",
        alias="AUTH_LOCKOUT_DURATION_MINUTES",
    )
    auth_ip_lockout_threshold: int = Field(
        default=50,
        description="Failed attempts per IP or /24 subnet per minute before throttling.",
        alias="AUTH_IP_LOCKOUT_THRESHOLD",
    )
    auth_ip_lockout_window_minutes: int = Field(
        default=10,
        description="Window in minutes used for IP-based throttling heuristics.",
        alias="AUTH_IP_LOCKOUT_WINDOW_MINUTES",
    )
    auth_ip_lockout_duration_minutes: int = Field(
        default=10,
        description="Duration in minutes to block an IP/subnet after threshold breaches.",
        alias="AUTH_IP_LOCKOUT_DURATION_MINUTES",
    )

    @property
    def jwks_max_age_seconds(self) -> int:
        return self.auth_jwks_max_age_seconds or self.auth_jwks_cache_seconds

    def secret_warnings(self) -> list[str]:
        warnings: list[str] = []
        if self._is_placeholder_secret(
            self.secret_key, {DEFAULT_SECRET_KEY, PLACEHOLDER_SECRET_KEY}
        ):
            warnings.append("SECRET_KEY is using the starter value")
        if self._is_placeholder_secret(
            self.auth_password_pepper,
            {DEFAULT_PASSWORD_PEPPER, PLACEHOLDER_PASSWORD_PEPPER},
        ):
            warnings.append("AUTH_PASSWORD_PEPPER is using the starter value")
        if self._is_placeholder_secret(
            self.auth_refresh_token_pepper,
            {DEFAULT_REFRESH_TOKEN_PEPPER, PLACEHOLDER_REFRESH_TOKEN_PEPPER},
        ):
            warnings.append("AUTH_REFRESH_TOKEN_PEPPER is using the starter value")
        if (
            self.auth_key_storage_backend == "file"
            and _is_default_key_path(self.auth_key_storage_path)
        ):
            warnings.append("AUTH_KEY_STORAGE_PATH still points to var/keys/keyset.json")
        if self.enable_resend_email_delivery:
            if not (self.resend_api_key and self.resend_api_key.strip()):
                warnings.append(
                    "RESEND_API_KEY must be configured when RESEND_EMAIL_ENABLED is true"
                )
            if not (self.resend_default_from and self.resend_default_from.strip()):
                warnings.append(
                    "RESEND_DEFAULT_FROM must be configured when RESEND_EMAIL_ENABLED is true"
                )
        return warnings

    @staticmethod
    def _is_placeholder_secret(value: str | None, placeholders: set[str]) -> bool:
        if value is None:
            return True
        normalized = value.strip()
        if not normalized:
            return True
        return normalized in placeholders

    def should_enforce_secret_overrides(self) -> bool:
        env = str(getattr(self, "environment", "") or "").lower()
        debug_mode = bool(getattr(self, "debug", False))
        return not debug_mode and env not in SAFE_ENVIRONMENTS

    def requires_secret_manager_for_key_storage(self) -> bool:
        env = str(getattr(self, "environment", "") or "").lower()
        debug_mode = bool(getattr(self, "debug", False))
        return not debug_mode and env not in SAFE_ENVIRONMENTS

    @field_validator("auth_audience", mode="before")
    @classmethod
    def _parse_auth_audience(
        cls, value: str | list[str] | tuple[str, ...] | set[str] | None
    ) -> list[str] | None:
        parsed = BaseAppSettings.parse_auth_audience_value(value)
        return parsed

    @field_validator("auth_key_storage_backend")
    @classmethod
    def _validate_key_storage_backend(cls, value: str) -> str:
        allowed = {"file", "secret-manager"}
        lowered = value.strip().lower()
        if lowered not in allowed:
            raise ValueError(f"auth_key_storage_backend must be one of {sorted(allowed)}")
        return lowered

    @field_validator("auth_jwks_cache_seconds")
    @classmethod
    def _positive_int(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Configuration value must be greater than zero.")
        return value

    @field_validator("auth_key_storage_path")
    @classmethod
    def _normalize_key_storage_path(cls, value: str) -> str:
        if not value:
            return value
        return str(resolve_repo_path(value))

    @field_validator("contact_email_recipients", mode="before")
    @classmethod
    def _parse_contact_recipients(cls, value: Any) -> list[str]:
        recipients = _parse_email_list(value)
        if not recipients:
            return ["support@localhost"]
        return recipients

    @field_validator("contact_email_subject_prefix")
    @classmethod
    def _normalize_contact_subject_prefix(cls, value: str) -> str:
        normalized = value.strip()
        return normalized or "[Contact]"


def _parse_email_list(value: Any) -> list[str]:
    if value in (None, "", []):
        return []
    raw_list: list[str]
    if isinstance(value, str):
        trimmed = value.strip()
        if not trimmed:
            return []
        try:
            parsed = json.loads(trimmed)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            raw_list = [str(item) for item in parsed]
        else:
            raw_list = list(trimmed.split(","))
    elif isinstance(value, list | tuple | set):
        raw_list = [str(item) for item in value]
    else:
        raise ValueError("Recipient list must be a string or sequence.")

    normalized: list[str] = []
    for entry in raw_list:
        candidate = entry.strip()
        if candidate and candidate not in normalized:
            normalized.append(candidate)
    return normalized


def _is_default_key_path(value: str) -> bool:
    if not value:
        return False
    candidate = Path(value).expanduser()
    default = resolve_repo_path(DEFAULT_KEY_STORAGE_PATH)
    try:
        return candidate.resolve() == default.resolve()
    except OSError:
        return candidate == default
