from __future__ import annotations

import json
import os

from starter_cli.cli.common import CLIError
from starter_cli.cli.console import console
from starter_cli.cli.setup._wizard.context import WizardContext
from starter_cli.cli.setup.inputs import InputProvider
from starter_cli.cli.setup.validators import validate_plan_map, validate_redis_url


def run(context: WizardContext, provider: InputProvider) -> None:
    console.info("[M2] Providers & Infra", topic="wizard")
    collect_database(context, provider)
    _collect_ai_providers(context, provider)
    _collect_redis(context, provider)
    _collect_billing(context, provider)
    _collect_email(context, provider)
    _maybe_run_migrations(context, provider)


def collect_database(context: WizardContext, provider: InputProvider) -> None:
    existing_url = context.current("DATABASE_URL") or os.getenv("DATABASE_URL")
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

    billing = provider.prompt_string(
        key="BILLING_EVENTS_REDIS_URL",
        prompt="Billing events Redis URL (blank = reuse primary)",
        default=context.current("BILLING_EVENTS_REDIS_URL") or "",
        required=False,
    )
    if billing:
        validate_redis_url(billing, require_tls=context.profile != "local", role="Billing events")
        context.set_backend("BILLING_EVENTS_REDIS_URL", billing)
    else:
        context.set_backend("BILLING_EVENTS_REDIS_URL", "")
        if context.profile != "local":
            console.warn(
                "Using the primary Redis instance for billing streams. Provision a dedicated "
                "instance for production.",
                topic="redis",
            )


def _collect_billing(context: WizardContext, provider: InputProvider) -> None:
    enable_billing = provider.prompt_bool(
        key="ENABLE_BILLING",
        prompt="Enable billing endpoints now?",
        default=context.current_bool("ENABLE_BILLING", False),
    )
    context.set_backend_bool("ENABLE_BILLING", enable_billing)

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

    if context.is_headless:
        console.warn(
            "Headless run detected. Run `python -m starter_cli.cli stripe setup` manually to seed "
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
        context.run_subprocess(
            ["python", "-m", "starter_cli.cli", "stripe", "setup"],
            topic="stripe",
        )


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


def _maybe_run_migrations(context: WizardContext, provider: InputProvider) -> None:
    run_now = provider.prompt_bool(
        key="RUN_MIGRATIONS_NOW",
        prompt="Run `make migrate` now?",
        default=context.profile != "local",
    )
    if run_now:
        context.run_migrations()
