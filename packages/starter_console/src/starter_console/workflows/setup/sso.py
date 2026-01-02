from __future__ import annotations

from starter_console.core import CLIError
from starter_console.services.sso import (
    CUSTOM_PRESET,
    SsoProviderSeedConfig,
    find_preset,
    preset_defaults,
    resolve_enabled_providers,
)
from starter_console.services.sso.config import build_config_from_env
from starter_console.services.sso.setup import run_sso_setup

from ._wizard.context import WizardContext
from .automation import AutomationPhase, AutomationStatus


def _resolve_configs(context: WizardContext) -> list[SsoProviderSeedConfig]:
    env_snapshot = context.backend_env.as_dict()
    provider_keys = resolve_enabled_providers(env_snapshot)
    if not provider_keys:
        return []

    configs: list[SsoProviderSeedConfig] = []
    for provider_key in provider_keys:
        preset = find_preset(provider_key) or CUSTOM_PRESET
        defaults = preset_defaults(preset)
        config = build_config_from_env(
            env_snapshot,
            provider_key=provider_key,
            defaults=defaults,
            enabled_default=True,
            enforce_enabled_flag=False,
        )
        if config is not None:
            configs.append(config)
    return configs


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
        configs = _resolve_configs(context)
    except CLIError as exc:
        context.automation.update(
            AutomationPhase.SSO,
            AutomationStatus.FAILED,
            f"SSO config invalid: {exc}",
        )
        context.refresh_automation_ui(AutomationPhase.SSO)
        context.console.error(f"SSO config invalid: {exc}", topic="sso")
        return

    if not configs:
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
        f"Seeding {len(configs)} SSO provider config(s).",
    )
    context.refresh_automation_ui(AutomationPhase.SSO)

    for config in configs:
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
        else:
            context.record_verification(
                provider="sso",
                identifier=config.provider_key,
                status="passed",
                detail="SSO provider config seeded.",
                source="wizard",
            )

    context.automation.update(
        AutomationPhase.SSO,
        AutomationStatus.SUCCEEDED,
        "SSO provider(s) seeded.",
    )
    context.refresh_automation_ui(AutomationPhase.SSO)


__all__ = ["run_sso_automation"]
