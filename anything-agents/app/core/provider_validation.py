"""Validation helpers for third-party provider configuration."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

_DOC_PATH = "docs/ops/provider-parity.md"


@dataclass(slots=True)
class ProviderViolation:
    """Represents a missing or invalid provider configuration item."""

    provider: str
    code: str
    message: str
    fatal: bool

    def as_log_message(self) -> str:
        scope = self.provider.upper()
        return f"[{scope}] {self.message}"


class ProviderSettingsProtocol(Protocol):
    enable_billing: bool
    enable_resend_email_delivery: bool
    resend_api_key: str | None
    resend_default_from: str | None
    tavily_api_key: str | None

    def should_enforce_secret_overrides(self) -> bool: ...

    def required_stripe_envs_missing(self) -> list[str]: ...


def validate_providers(
    settings: ProviderSettingsProtocol,
    *,
    strict: bool | None = None,
) -> list[ProviderViolation]:
    """Return all validation failures for configured external providers."""

    strict_mode = settings.should_enforce_secret_overrides() if strict is None else strict
    violations: list[ProviderViolation] = []

    violations.extend(_validate_stripe(settings, strict_mode))
    violations.extend(_validate_resend(settings, strict_mode))
    violations.extend(_validate_tavily(settings, strict_mode))

    return violations


def ensure_provider_parity(
    settings: ProviderSettingsProtocol,
    *,
    violations: list[ProviderViolation] | None = None,
) -> list[ProviderViolation]:
    """Validate providers and raise when fatal issues are detected."""

    evaluated = violations or validate_providers(settings)
    fatal = [violation for violation in evaluated if violation.fatal]
    if fatal:
        summary = "; ".join(f"{item.provider}:{item.code}" for item in fatal)
        raise RuntimeError(
            "Third-party providers are misconfigured "
            f"({summary}). See {_DOC_PATH} for remediation steps."
        )
    return evaluated


def _validate_stripe(
    settings: ProviderSettingsProtocol,
    strict: bool,
) -> Iterable[ProviderViolation]:
    if not settings.enable_billing:
        return []

    missing = settings.required_stripe_envs_missing()
    violations: list[ProviderViolation] = []
    for env_name in missing:
        violations.append(
            ProviderViolation(
                provider="stripe",
                code=f"missing_{env_name.lower()}",
                message=f"ENABLE_BILLING=true requires {env_name}.",
                fatal=strict,
            )
        )
    return violations


def _validate_resend(
    settings: ProviderSettingsProtocol,
    strict: bool,
) -> Iterable[ProviderViolation]:
    if not settings.enable_resend_email_delivery:
        return []

    violations: list[ProviderViolation] = []
    if not (settings.resend_api_key and settings.resend_api_key.strip()):
        violations.append(
            ProviderViolation(
                provider="resend",
                code="missing_resend_api_key",
                message="RESEND_EMAIL_ENABLED=true requires RESEND_API_KEY.",
                fatal=strict,
            )
        )
    if not (settings.resend_default_from and settings.resend_default_from.strip()):
        violations.append(
            ProviderViolation(
                provider="resend",
                code="missing_resend_default_from",
                message="RESEND_EMAIL_ENABLED=true requires RESEND_DEFAULT_FROM.",
                fatal=strict,
            )
        )
    return violations


def _validate_tavily(
    settings: ProviderSettingsProtocol,
    strict: bool,
) -> Iterable[ProviderViolation]:
    if settings.tavily_api_key and settings.tavily_api_key.strip():
        return []

    return [
        ProviderViolation(
            provider="tavily",
            code="missing_tavily_api_key",
            message="Web search tools require TAVILY_API_KEY. Agents will continue "
            "without the Tavily tool when this value is unset.",
            fatal=strict,
        )
    ]


__all__ = [
    "ProviderSettingsProtocol",
    "ProviderViolation",
    "ensure_provider_parity",
    "validate_providers",
]
