from __future__ import annotations

from starter_console.core import CLIError
from starter_console.services.sso import (
    DEFAULT_SCOPES,
    GOOGLE_DISCOVERY_URL,
    GOOGLE_ISSUER_URL,
    GOOGLE_PROVIDER_KEY,
    SsoProviderSeedConfig,
)
from starter_console.services.sso.config import build_config_from_env
from starter_console.services.sso.setup import run_sso_setup

from ._wizard.context import WizardContext
from .automation import AutomationPhase, AutomationStatus


def _resolve_config(context: WizardContext) -> SsoProviderSeedConfig | None:
    env_snapshot = context.backend_env.as_dict()
    return build_config_from_env(
        env_snapshot,
        provider_key=GOOGLE_PROVIDER_KEY,
        defaults={
            "issuer_url": GOOGLE_ISSUER_URL,
            "discovery_url": GOOGLE_DISCOVERY_URL,
            "scopes": ",".join(DEFAULT_SCOPES),
        },
    )


def run_sso_automation(context: WizardContext) -> None:
    record = context.automation.get(AutomationPhase.SSO)
    if not record.enabled:
        return
    if record.status == AutomationStatus.BLOCKED:
        context.console.warn(record.note or "SSO automation blocked.", topic="sso")
        context.refresh_automation_ui(AutomationPhase.SSO)
        return

    migrations_record = context.automation.get(AutomationPhase.MIGRATIONS)
    if migrations_record.enabled and migrations_record.status not in {
        AutomationStatus.SUCCEEDED,
        AutomationStatus.SKIPPED,
    }:
        context.automation.update(
            AutomationPhase.SSO,
            AutomationStatus.BLOCKED,
            "SSO seeding waits for migrations to complete.",
        )
        context.refresh_automation_ui(AutomationPhase.SSO)
        context.console.warn(
            "SSO automation blocked until migrations succeed.",
            topic="sso",
        )
        return

    try:
        config = _resolve_config(context)
    except CLIError as exc:
        context.automation.update(
            AutomationPhase.SSO,
            AutomationStatus.FAILED,
            f"SSO config invalid: {exc}",
        )
        context.refresh_automation_ui(AutomationPhase.SSO)
        context.console.error(f"SSO config invalid: {exc}", topic="sso")
        return

    if config is None:
        context.automation.update(
            AutomationPhase.SSO,
            AutomationStatus.SKIPPED,
            "SSO not enabled; skipping seed.",
        )
        context.refresh_automation_ui(AutomationPhase.SSO)
        return

    context.automation.update(
        AutomationPhase.SSO,
        AutomationStatus.RUNNING,
        "Seeding SSO provider config.",
    )
    context.refresh_automation_ui(AutomationPhase.SSO)

    try:
        run_sso_setup(context.cli_ctx, config=config, update_env=False)
    except CLIError as exc:
        context.automation.update(
            AutomationPhase.SSO,
            AutomationStatus.FAILED,
            f"SSO seed failed: {exc}",
        )
        context.refresh_automation_ui(AutomationPhase.SSO)
        context.console.error(f"SSO seed failed: {exc}", topic="sso")
        return

    context.automation.update(
        AutomationPhase.SSO,
        AutomationStatus.SUCCEEDED,
        "SSO provider seeded.",
    )
    context.refresh_automation_ui(AutomationPhase.SSO)
    context.record_verification(
        provider="sso",
        identifier=config.provider_key,
        status="passed",
        detail="SSO provider config seeded.",
        source="wizard",
    )


__all__ = ["run_sso_automation"]
