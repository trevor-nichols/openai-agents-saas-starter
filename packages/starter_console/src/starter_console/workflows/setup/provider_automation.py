from __future__ import annotations

import subprocess

from starter_console.adapters.redis_health import RedisHealthAdapter
from starter_console.core import CLIError
from starter_console.ports.redis import RedisHealthPort

from ._wizard.context import WizardContext
from .automation import AutomationPhase, AutomationStatus


def run_provider_automation(
    context: WizardContext,
    *,
    redis_health: RedisHealthPort | None = None,
) -> None:
    plan = context.provider_automation_plan
    redis_health = redis_health or RedisHealthAdapter()

    if plan.redis_targets:
        _run_redis_warmup(context, redis_health, plan.redis_targets)
    _run_migrations(context, manual=plan.run_migrations)
    _run_stripe_setup(context, manual=plan.run_stripe_setup)


def _run_redis_warmup(
    context: WizardContext,
    redis_health: RedisHealthPort,
    targets: dict[str, str],
) -> None:
    record = context.automation.get(AutomationPhase.REDIS)
    if not record.enabled:
        return
    if record.status == AutomationStatus.BLOCKED:
        context.console.warn(record.note or "Redis automation blocked.", topic="redis")
        context.refresh_automation_ui(AutomationPhase.REDIS)
        return
    context.automation.update(
        AutomationPhase.REDIS,
        AutomationStatus.RUNNING,
        "Validating Redis connectivity.",
    )
    context.refresh_automation_ui(AutomationPhase.REDIS)
    try:
        redis_health.ping_all(targets.values())
    except Exception as exc:  # pragma: no cover - network failures
        context.automation.update(
            AutomationPhase.REDIS,
            AutomationStatus.FAILED,
            f"Redis warm-up failed: {exc}",
        )
        context.refresh_automation_ui(AutomationPhase.REDIS)
        raise CLIError(f"Redis warm-up failed: {exc}") from exc
    else:
        context.automation.update(
            AutomationPhase.REDIS,
            AutomationStatus.SUCCEEDED,
            "Redis warm-up succeeded.",
        )
        context.refresh_automation_ui(AutomationPhase.REDIS)
        context.console.success("Redis pools validated.", topic="redis")


def _run_migrations(context: WizardContext, *, manual: bool) -> None:
    record = context.automation.get(AutomationPhase.MIGRATIONS)
    if record.enabled:
        if record.status == AutomationStatus.BLOCKED:
            context.console.warn(record.note or "Migrations automation blocked.", topic="migrate")
            context.refresh_automation_ui(AutomationPhase.MIGRATIONS)
            return
        context.automation.update(
            AutomationPhase.MIGRATIONS,
            AutomationStatus.RUNNING,
            "Running `just migrate`.",
        )
        context.refresh_automation_ui(AutomationPhase.MIGRATIONS)
        try:
            context.run_migrations()
        except (CLIError, subprocess.CalledProcessError) as exc:
            context.automation.update(
                AutomationPhase.MIGRATIONS,
                AutomationStatus.FAILED,
                f"Migrations failed: {exc}",
            )
            context.refresh_automation_ui(AutomationPhase.MIGRATIONS)
            raise
        else:
            context.automation.update(
                AutomationPhase.MIGRATIONS,
                AutomationStatus.SUCCEEDED,
                "Database migrated.",
            )
            context.refresh_automation_ui(AutomationPhase.MIGRATIONS)
        return

    if not manual:
        return
    context.run_migrations()


def _run_stripe_setup(context: WizardContext, *, manual: bool) -> None:
    if not context.current_bool("ENABLE_BILLING", False):
        record = context.automation.get(AutomationPhase.STRIPE)
        if record.enabled:
            context.automation.update(
                AutomationPhase.STRIPE,
                AutomationStatus.SKIPPED,
                "Billing disabled; skipping Stripe setup.",
            )
            context.refresh_automation_ui(AutomationPhase.STRIPE)
        return

    record = context.automation.get(AutomationPhase.STRIPE)
    if record.enabled:
        if record.status == AutomationStatus.BLOCKED:
            context.console.warn(
                f"Stripe automation blocked: {record.note or 'unmet prerequisites.'}",
                topic="stripe",
            )
            return
        if context.is_headless:
            context.console.warn(
                "Stripe automation skipped in headless mode; run the setup command manually.",
                topic="stripe",
            )
            context.automation.update(
                AutomationPhase.STRIPE,
                AutomationStatus.SKIPPED,
                "Headless mode skips Stripe automation.",
            )
            context.refresh_automation_ui(AutomationPhase.STRIPE)
            return
        context.automation.update(
            AutomationPhase.STRIPE,
            AutomationStatus.RUNNING,
            "Running `stripe setup` helper.",
        )
        context.refresh_automation_ui(AutomationPhase.STRIPE)
        context.console.info("Running embedded Stripe setup flow …", topic="stripe")
        try:
            context.run_subprocess(
                ["python", "-m", "starter_console.app", "stripe", "setup"],
                topic="stripe",
            )
        except (CLIError, subprocess.CalledProcessError) as exc:
            context.automation.update(
                AutomationPhase.STRIPE,
                AutomationStatus.FAILED,
                f"Stripe setup failed: {exc}",
            )
            context.refresh_automation_ui(AutomationPhase.STRIPE)
            raise
        else:
            context.automation.update(
                AutomationPhase.STRIPE,
                AutomationStatus.SUCCEEDED,
                "Stripe setup completed.",
            )
            context.refresh_automation_ui(AutomationPhase.STRIPE)
            context.record_verification(
                provider="stripe",
                identifier="stripe_setup",
                status="passed",
                detail="Plans seeded via CLI.",
                source="wizard",
            )
        return

    if not manual:
        return
    if context.is_headless:
        context.console.warn(
            "Headless run detected. Run `starter-console stripe setup` manually to seed "
            "plans.",
            topic="stripe",
        )
        return

    try:
        context.run_subprocess(
            ["python", "-m", "starter_console.app", "stripe", "setup"],
            topic="stripe",
        )
    except (CLIError, subprocess.CalledProcessError) as exc:
        context.record_verification(
            provider="stripe",
            identifier="stripe_setup",
            status="failed",
            detail=str(exc),
            source="wizard",
        )
        raise
    else:
        context.record_verification(
            provider="stripe",
            identifier="stripe_setup",
            status="passed",
            detail="Plans seeded via CLI.",
            source="wizard",
        )


__all__ = ["run_provider_automation"]
