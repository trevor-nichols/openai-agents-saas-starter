from __future__ import annotations

import json

from starter_console.adapters.stripe_webhook import StripeWebhookCaptureAdapter
from starter_console.core import CLIError
from starter_console.ports.stripe import StripeWebhookCapturePort

from ....automation import AutomationPhase
from ....inputs import InputProvider
from ....validators import validate_plan_map
from ...context import WizardContext


def collect_billing(context: WizardContext, provider: InputProvider) -> None:
    enable_billing = provider.prompt_bool(
        key="ENABLE_BILLING",
        prompt="Enable billing endpoints now?",
        default=context.policy_env_default_bool("ENABLE_BILLING", fallback=False),
    )
    context.set_backend_bool("ENABLE_BILLING", enable_billing)

    enable_stream = provider.prompt_bool(
        key="ENABLE_BILLING_STREAM",
        prompt="Enable billing stream (Redis SSE)?",
        default=context.policy_env_default_bool("ENABLE_BILLING_STREAM", fallback=False),
    )
    context.set_backend_bool("ENABLE_BILLING_STREAM", enable_stream)

    if not enable_billing:
        context.console.info("Stripe secrets skipped (ENABLE_BILLING=false).", topic="wizard")
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

    _request_stripe_setup(context, provider)


def _maybe_generate_webhook_secret(
    context: WizardContext,
    provider: InputProvider,
    *,
    webhook_capture: StripeWebhookCapturePort | None = None,
) -> str | None:
    allow_auto = context.policy_rule_bool("stripe_webhook_auto_allowed", fallback=False)
    allow_auto = allow_auto and not context.is_headless
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
        if context.cli_ctx.presenter is None:  # pragma: no cover - defensive
            raise CLIError("Presenter not initialized.")
        prompt = context.cli_ctx.presenter.prompt
        webhook_capture = webhook_capture or StripeWebhookCaptureAdapter(
            console=context.console,
            prompt=prompt,
            non_interactive=False,
        )
        secret = webhook_capture.capture_webhook_secret(forward_url=forward_url)
    except CLIError as exc:
        context.console.warn(f"Stripe CLI webhook capture failed: {exc}", topic="stripe")
        return None

    context.console.success("Captured webhook signing secret via Stripe CLI.", topic="stripe")
    return secret


def _request_stripe_setup(context: WizardContext, provider: InputProvider) -> None:
    record = context.automation.get(AutomationPhase.STRIPE)
    if record.enabled:
        return
    if context.is_headless:
        context.console.warn(
            "Headless run detected. Run `starter-console stripe setup` manually to seed "
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
        context.provider_automation_plan.run_stripe_setup = True


__all__ = ["collect_billing"]
