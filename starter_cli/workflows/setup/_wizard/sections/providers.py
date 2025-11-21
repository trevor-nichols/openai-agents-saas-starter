from __future__ import annotations

import asyncio
import json
import os
import subprocess

from redis.asyncio import Redis

from starter_cli.adapters.io.console import console
from starter_cli.commands.stripe import WebhookSecretFlow
from starter_cli.core import CLIError

from ...automation import AutomationPhase, AutomationStatus
from ...inputs import InputProvider
from ...validators import validate_plan_map, validate_redis_url
from ..context import WizardContext


def run(context: WizardContext, provider: InputProvider) -> None:
    console.section(
        "Providers & Infra",
        "Wire up databases, AI providers, Redis, billing, and email transports.",
    )
    collect_database(context, provider)
    _collect_ai_providers(context, provider)
    _collect_redis(context, provider)
    _collect_billing(context, provider)
    _collect_email(context, provider)
    _maybe_run_migrations(context, provider)


def collect_database(context: WizardContext, provider: InputProvider) -> None:
    existing_url = context.current("DATABASE_URL") or os.getenv("DATABASE_URL")
    default_url: str | None
    if context.profile == "local":
        default_url = (
            existing_url
            or "postgresql+asyncpg://postgres:postgres@localhost:5432/anything_agents"
        )
    else:
        default_url = existing_url
    required = context.profile != "local"
    db_url = provider.prompt_string(
        key="DATABASE_URL",
        prompt="Primary Postgres connection URL (DATABASE_URL)",
        default=default_url,
        required=required,
    )
    if db_url:
        context.set_backend("DATABASE_URL", db_url)
        return
    if required:
        raise CLIError("DATABASE_URL is required outside local profiles.")

    console.warn(
        "DATABASE_URL left blank; Compose defaults will be used for local dev.",
        topic="database",
    )
    context.unset_backend("DATABASE_URL")


def _collect_ai_providers(context: WizardContext, provider: InputProvider) -> None:
    openai_key = provider.prompt_secret(
        key="OPENAI_API_KEY",
        prompt="OpenAI API key (required)",
        existing=context.current("OPENAI_API_KEY"),
        required=True,
    )
    context.set_backend("OPENAI_API_KEY", openai_key, mask=True)

    for key, label in (
        ("ANTHROPIC_API_KEY", "Anthropic API key"),
        ("GEMINI_API_KEY", "Google Gemini API key"),
        ("XAI_API_KEY", "xAI API key"),
    ):
        default_enabled = bool(context.current(key))
        if provider.prompt_bool(
            key=f"ENABLE_{key}",
            prompt=f"Configure {label}?",
            default=default_enabled,
        ):
            value = provider.prompt_secret(
                key=key,
                prompt=label,
                existing=context.current(key),
                required=False,
            )
            if value:
                context.set_backend(key, value, mask=True)
            else:
                context.set_backend(key, "")
        else:
            context.set_backend(key, "")

    if provider.prompt_bool(
        key="ENABLE_TAVILY",
        prompt="Enable Tavily search tools?",
        default=bool(context.current("TAVILY_API_KEY")),
    ):
        tavily_key = provider.prompt_secret(
            key="TAVILY_API_KEY",
            prompt="Tavily API key",
            existing=context.current("TAVILY_API_KEY"),
            required=False,
        )
        if tavily_key:
            context.set_backend("TAVILY_API_KEY", tavily_key, mask=True)
        else:
            context.set_backend("TAVILY_API_KEY", "")
    else:
        context.set_backend("TAVILY_API_KEY", "")


def _collect_redis(context: WizardContext, provider: InputProvider) -> None:
    primary = provider.prompt_string(
        key="REDIS_URL",
        prompt="Primary Redis URL",
        default=context.current("REDIS_URL") or "redis://localhost:6379/0",
        required=True,
    )
    validate_redis_url(primary, require_tls=context.profile != "local", role="Primary")
    context.set_backend("REDIS_URL", primary)
    redis_targets: dict[str, str] = {"Primary": primary}

    def _configure_optional(key: str, label: str) -> None:
        value = provider.prompt_string(
            key=key,
            prompt=f"{label} Redis URL (blank = reuse primary)",
            default=context.current(key) or "",
            required=False,
        )
        if value:
            validate_redis_url(value, require_tls=context.profile != "local", role=label)
            context.set_backend(key, value)
            redis_targets[label] = value
        else:
            context.set_backend(key, "")
            if context.profile != "local":
                console.warn(
                    f"{label} Redis workloads will reuse the primary Redis instance. "
                    "Provision a dedicated pool in production.",
                    topic="redis",
                )

    _configure_optional("RATE_LIMIT_REDIS_URL", "Rate limiting")
    _configure_optional("AUTH_CACHE_REDIS_URL", "Auth/session cache")
    _configure_optional("SECURITY_TOKEN_REDIS_URL", "Security token")

    billing = provider.prompt_string(
        key="BILLING_EVENTS_REDIS_URL",
        prompt="Billing events Redis URL (blank = reuse primary)",
        default=context.current("BILLING_EVENTS_REDIS_URL") or "",
        required=False,
    )
    if billing:
        validate_redis_url(billing, require_tls=context.profile != "local", role="Billing events")
        context.set_backend("BILLING_EVENTS_REDIS_URL", billing)
        redis_targets["Billing events"] = billing
    else:
        context.set_backend("BILLING_EVENTS_REDIS_URL", "")
        if context.profile != "local":
            console.warn(
                "Using the primary Redis instance for billing streams. Provision a dedicated "
                "instance for production.",
                topic="redis",
            )
    _warmup_redis(context, redis_targets)


def _collect_billing(context: WizardContext, provider: InputProvider) -> None:
    enable_billing = provider.prompt_bool(
        key="ENABLE_BILLING",
        prompt="Enable billing endpoints now?",
        default=context.current_bool("ENABLE_BILLING", False),
    )
    context.set_backend_bool("ENABLE_BILLING", enable_billing)
    context.set_frontend_bool("NEXT_PUBLIC_ENABLE_BILLING", enable_billing)

    enable_stream = provider.prompt_bool(
        key="ENABLE_BILLING_STREAM",
        prompt="Enable billing stream (Redis SSE)?",
        default=context.current_bool("ENABLE_BILLING_STREAM", False),
    )
    context.set_backend_bool("ENABLE_BILLING_STREAM", enable_stream)

    if not enable_billing:
        console.info("Stripe secrets skipped (ENABLE_BILLING=false).", topic="wizard")
        return

    secret = provider.prompt_secret(
        key="STRIPE_SECRET_KEY",
        prompt="Stripe secret key",
        existing=context.current("STRIPE_SECRET_KEY"),
        required=True,
    )
    webhook = _maybe_generate_webhook_secret(context, provider)
    if not webhook:
        webhook = provider.prompt_secret(
            key="STRIPE_WEBHOOK_SECRET",
            prompt="Stripe webhook signing secret",
            existing=context.current("STRIPE_WEBHOOK_SECRET"),
            required=True,
        )
    plan_map_raw = provider.prompt_string(
        key="STRIPE_PRODUCT_PRICE_MAP",
        prompt="Stripe product price map (JSON)",
        default=(
            context.current("STRIPE_PRODUCT_PRICE_MAP")
            or '{"starter":"price_xxx","pro":"price_xxx"}'
        ),
        required=True,
    )
    validated = validate_plan_map(plan_map_raw)
    context.set_backend("STRIPE_SECRET_KEY", secret, mask=True)
    context.set_backend("STRIPE_WEBHOOK_SECRET", webhook, mask=True)
    context.set_backend(
        "STRIPE_PRODUCT_PRICE_MAP",
        json.dumps(validated, separators=(",", ":")),
    )

    _maybe_run_stripe_setup(context, provider)


def _maybe_generate_webhook_secret(context: WizardContext, provider: InputProvider) -> str | None:
    allow_auto = context.profile == "local" and not context.is_headless
    if not allow_auto:
        return None

    default_yes = not bool(context.current("STRIPE_WEBHOOK_SECRET"))
    if not provider.prompt_bool(
        key="STRIPE_WEBHOOK_SECRET_AUTO",
        prompt="Generate webhook signing secret via Stripe CLI now?",
        default=default_yes,
    ):
        return None

    forward_url = f"{context.api_base_url.rstrip('/')}/api/v1/webhooks/stripe"
    try:
        flow = WebhookSecretFlow(
            ctx=context.cli_ctx,
            forward_url=forward_url,
            print_only=True,
            skip_stripe_cli=False,
        )
        secret = flow._capture_webhook_secret(forward_url)
    except CLIError as exc:
        console.warn(f"Stripe CLI webhook capture failed: {exc}", topic="stripe")
        return None

    console.success("Captured webhook signing secret via Stripe CLI.", topic="stripe")
    return secret


def _collect_email(context: WizardContext, provider: InputProvider) -> None:
    enable_resend = provider.prompt_bool(
        key="RESEND_EMAIL_ENABLED",
        prompt="Enable Resend email delivery?",
        default=context.current_bool("RESEND_EMAIL_ENABLED", False),
    )
    context.set_backend_bool("RESEND_EMAIL_ENABLED", enable_resend)
    base_url = provider.prompt_string(
        key="RESEND_BASE_URL",
        prompt="Resend API base URL",
        default=context.current("RESEND_BASE_URL") or "https://api.resend.com",
        required=True,
    )
    context.set_backend("RESEND_BASE_URL", base_url)
    if not enable_resend:
        return

    api_key = provider.prompt_secret(
        key="RESEND_API_KEY",
        prompt="Resend API key",
        existing=context.current("RESEND_API_KEY"),
        required=True,
    )
    default_from = provider.prompt_string(
        key="RESEND_DEFAULT_FROM",
        prompt="Default From address",
        default=context.current("RESEND_DEFAULT_FROM") or "support@example.com",
        required=True,
    )
    template_verify = provider.prompt_string(
        key="RESEND_EMAIL_VERIFICATION_TEMPLATE_ID",
        prompt="Verification template ID (optional)",
        default=context.current("RESEND_EMAIL_VERIFICATION_TEMPLATE_ID") or "",
        required=False,
    )
    template_reset = provider.prompt_string(
        key="RESEND_PASSWORD_RESET_TEMPLATE_ID",
        prompt="Password reset template ID (optional)",
        default=context.current("RESEND_PASSWORD_RESET_TEMPLATE_ID") or "",
        required=False,
    )
    context.set_backend("RESEND_API_KEY", api_key, mask=True)
    context.set_backend("RESEND_DEFAULT_FROM", default_from)
    context.set_backend("RESEND_EMAIL_VERIFICATION_TEMPLATE_ID", template_verify)
    context.set_backend("RESEND_PASSWORD_RESET_TEMPLATE_ID", template_reset)

def _warmup_redis(context: WizardContext, targets: dict[str, str]) -> None:
    record = context.automation.get(AutomationPhase.REDIS)
    if not record.enabled:
        return
    if record.status == AutomationStatus.BLOCKED:
        console.warn(record.note or "Redis automation blocked.", topic="redis")
        context.refresh_automation_ui(AutomationPhase.REDIS)
        return
    context.automation.update(
        AutomationPhase.REDIS,
        AutomationStatus.RUNNING,
        "Validating Redis connectivity.",
    )
    context.refresh_automation_ui(AutomationPhase.REDIS)
    try:
        asyncio.run(_ping_all_redis(targets))
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
        console.success("Redis pools validated.", topic="redis")


async def _ping_all_redis(targets: dict[str, str]) -> None:
    seen: set[str] = set()
    for _, url in targets.items():
        if not url or url in seen:
            continue
        seen.add(url)
        client = Redis.from_url(url, encoding="utf-8", decode_responses=True)
        try:
            await client.ping()
        finally:
            await client.close()


def _maybe_run_migrations(context: WizardContext, provider: InputProvider) -> None:
    record = context.automation.get(AutomationPhase.MIGRATIONS)
    if record.enabled:
        if record.status == AutomationStatus.BLOCKED:
            console.warn(record.note or "Migrations automation blocked.", topic="migrate")
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

    run_now = provider.prompt_bool(
        key="RUN_MIGRATIONS_NOW",
        prompt="Run `just migrate` now?",
        default=context.profile != "local",
    )
    if run_now:
        context.run_migrations()
def _maybe_run_stripe_setup(context: WizardContext, provider: InputProvider) -> None:
    record = context.automation.get(AutomationPhase.STRIPE)
    if record.enabled:
        if record.status == AutomationStatus.BLOCKED:
            console.warn(
                f"Stripe automation blocked: {record.note or 'unmet prerequisites.'}",
                topic="stripe",
            )
            return
        if context.is_headless:
            console.warn(
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
        console.info("Running embedded Stripe setup flow …", topic="stripe")
        try:
            context.run_subprocess(
                ["python", "-m", "starter_cli.app", "stripe", "setup"],
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

    if context.is_headless:
        console.warn(
            "Headless run detected. Run `python -m starter_cli.app stripe setup` manually to seed "
            "plans.",
            topic="stripe",
        )
        return

    should_seed = provider.prompt_bool(
        key="RUN_STRIPE_SEED",
        prompt="Run the Stripe setup helper now?",
        default=False,
    )
    if should_seed:
        try:
            context.run_subprocess(
                ["python", "-m", "starter_cli.app", "stripe", "setup"],
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
