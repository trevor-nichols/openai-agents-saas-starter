from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SectionSpec:
    key: str
    label: str
    summary: str


SECTION_SPECS: list[SectionSpec] = [
    SectionSpec(
        key="core",
        label="Profile & Core",
        summary="Choose hosting mode, then set baseline URLs, branding, and auth defaults.",
    ),
    SectionSpec(
        key="providers",
        label="Infra & Providers",
        summary="Wire databases, AI providers, Redis, billing, and email transports.",
    ),
    SectionSpec(
        key="secrets",
        label="Secrets & Key Management",
        summary="Generate peppers/keys, select the secrets provider, and rotate signing keys.",
    ),
    SectionSpec(
        key="security",
        label="Security & Rate Limits",
        summary="Configure lockouts, JWKS cache, and email/reset throttles.",
    ),
    SectionSpec(
        key="storage",
        label="Storage",
        summary="Select an object storage provider and configure credentials.",
    ),
    SectionSpec(
        key="usage",
        label="Usage & Entitlements",
        summary="Enable usage guardrails and capture per-plan limits for billing.",
    ),
    SectionSpec(
        key="observability",
        label="Tenant & Observability",
        summary="Set tenant defaults, logging sinks, and GeoIP provider posture.",
    ),
    SectionSpec(
        key="integrations",
        label="Integrations",
        summary="Connect Slack status notifications and other operator tooling.",
    ),
    SectionSpec(
        key="signup",
        label="Signup & Worker",
        summary="Choose signup access policy, throttles, and billing worker defaults.",
    ),
    SectionSpec(
        key="frontend",
        label="Frontend",
        summary="Finalize Next.js env config for API URLs, Playwright, and cookie posture.",
    ),
    SectionSpec(
        key="dev_user",
        label="Dev User",
        summary="Collect demo dev user defaults and credentials for seeding.",
    ),
]

SECTION_LABELS: dict[str, str] = {spec.key: spec.label for spec in SECTION_SPECS}


__all__ = ["SectionSpec", "SECTION_SPECS", "SECTION_LABELS"]
