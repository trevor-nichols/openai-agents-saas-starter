from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class SectionSpec:
    key: str
    label: str
    description: str
    detail: str
    shortcut: str


@dataclass(frozen=True, slots=True)
class NavGroupSpec:
    key: str
    label: str
    description: str
    items: tuple[SectionSpec, ...]
    collapsed: bool = False


NAV_GROUPS: Final[tuple[NavGroupSpec, ...]] = (
    NavGroupSpec(
        key="overview",
        label="Overview",
        description="Stack health, readiness checks, and setup status.",
        items=(
            SectionSpec(
                key="home",
                label="Home",
                description="Operational overview and quick actions.",
                detail="Status, health, and shortcuts for the starter stack.",
                shortcut="H",
            ),
            SectionSpec(
                key="setup",
                label="Setup Hub",
                description="Bootstrap secrets, env, and providers.",
                detail="Guided setup actions to get the stack production-ready.",
                shortcut="S",
            ),
            SectionSpec(
                key="doctor",
                label="Doctor",
                description="Readiness checks and audit exports.",
                detail="Run diagnostic probes and export JSON/Markdown reports.",
                shortcut="D",
            ),
        ),
    ),
    NavGroupSpec(
        key="onboarding",
        label="Onboarding",
        description="First-time setup workflows and provider onboarding.",
        items=(
            SectionSpec(
                key="wizard",
                label="Wizard",
                description="Interactive setup walkthrough.",
                detail="Step-by-step prompts for first-time configuration.",
                shortcut="W",
            ),
            SectionSpec(
                key="secrets",
                label="Secrets Onboarding",
                description="Configure signing and secrets providers.",
                detail="Choose a secrets provider and complete onboarding prompts.",
                shortcut="O",
            ),
            SectionSpec(
                key="providers",
                label="Providers Validation",
                description="External provider configuration checks.",
                detail="OpenAI, email, storage, and other integrations.",
                shortcut="P",
            ),
        ),
    ),
    NavGroupSpec(
        key="operations",
        label="Operations",
        description="Runtime controls, infra utilities, and logs.",
        items=(
            SectionSpec(
                key="start-stop",
                label="Start / Stop",
                description="Start local services and manage detached runs.",
                detail="Run dev targets, detach processes, and stop tracked stacks.",
                shortcut="T",
            ),
            SectionSpec(
                key="infra",
                label="Infra",
                description="Local stack status and controls.",
                detail="Compose services, vault, and supporting infra.",
                shortcut="I",
            ),
            SectionSpec(
                key="logs",
                label="Logs",
                description="Tail and filter local logs.",
                detail="Inspect API, frontend, and CLI logs with context.",
                shortcut="L",
            ),
        ),
    ),
    NavGroupSpec(
        key="security",
        label="Security & Auth",
        description="Token issuance and key management.",
        items=(
            SectionSpec(
                key="auth-tokens",
                label="Auth Tokens",
                description="Issue service-account tokens.",
                detail="Generate refresh tokens for automation and integrations.",
                shortcut="A",
            ),
            SectionSpec(
                key="key-rotation",
                label="Key Rotation",
                description="Rotate signing keys.",
                detail="Generate and activate new Ed25519 signing keys.",
                shortcut="K",
            ),
            SectionSpec(
                key="jwks",
                label="JWKS",
                description="Inspect JSON Web Key Sets.",
                detail="Print the current JWKS payload.",
                shortcut="J",
            ),
        ),
    ),
    NavGroupSpec(
        key="billing",
        label="Billing & Usage",
        description="Stripe setup, dispatches, and usage guardrails.",
        items=(
            SectionSpec(
                key="stripe",
                label="Stripe",
                description="Billing setup and webhooks.",
                detail="Keys, products, prices, and webhook verification.",
                shortcut="B",
            ),
            SectionSpec(
                key="usage",
                label="Usage",
                description="Usage reports and entitlements.",
                detail="Track token usage and sync guardrail entitlements.",
                shortcut="U",
            ),
        ),
    ),
    NavGroupSpec(
        key="release",
        label="Release & Admin",
        description="Release readiness and admin exports.",
        items=(
            SectionSpec(
                key="release-db",
                label="Release DB",
                description="Migrations and billing plan verification.",
                detail="Run database release automation with Stripe checks.",
                shortcut="R",
            ),
            SectionSpec(
                key="config-inventory",
                label="Config Inventory",
                description="Inspect backend settings schema.",
                detail="Dump schema and export inventory docs.",
                shortcut="C",
            ),
            SectionSpec(
                key="api-export",
                label="API Export",
                description="Export OpenAPI schema.",
                detail="Generate OpenAPI JSON artifacts with flags.",
                shortcut="E",
            ),
        ),
    ),
    NavGroupSpec(
        key="advanced",
        label="Advanced",
        description="Power-user workflows and status ops.",
        items=(
            SectionSpec(
                key="status-ops",
                label="Status Ops",
                description="Status subscriptions and incident resend.",
                detail="Manage status subscriptions and dispatch alerts.",
                shortcut="X",
            ),
            SectionSpec(
                key="util-run-with-env",
                label="Run With Env",
                description="Merge env files and exec commands.",
                detail="Run a command with merged env file values.",
                shortcut="V",
            ),
        ),
        collapsed=True,
    ),
)


def iter_sections(groups: tuple[NavGroupSpec, ...] = NAV_GROUPS) -> tuple[SectionSpec, ...]:
    return tuple(section for group in groups for section in group.items)


__all__ = ["NAV_GROUPS", "NavGroupSpec", "SectionSpec", "iter_sections"]
