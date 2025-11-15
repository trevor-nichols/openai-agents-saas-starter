from __future__ import annotations

from starter_cli.cli.console import console
from starter_cli.cli.setup._wizard.context import WizardContext
from starter_cli.cli.setup.inputs import InputProvider
from starter_cli.cli.setup.validators import parse_positive_int


def run(context: WizardContext, provider: InputProvider) -> None:
    console.info("[M4] Signup & Worker policy", topic="wizard")
    allow_public = provider.prompt_bool(
        key="ALLOW_PUBLIC_SIGNUP",
        prompt="Allow public signup?",
        default=context.current_bool("ALLOW_PUBLIC_SIGNUP", True),
    )
    context.set_backend_bool("ALLOW_PUBLIC_SIGNUP", allow_public)

    allow_override = provider.prompt_bool(
        key="ALLOW_SIGNUP_TRIAL_OVERRIDE",
        prompt="Allow clients to request custom trial lengths?",
        default=context.current_bool("ALLOW_SIGNUP_TRIAL_OVERRIDE", False),
    )
    context.set_backend_bool("ALLOW_SIGNUP_TRIAL_OVERRIDE", allow_override)

    rate_limit = parse_positive_int(
        provider.prompt_string(
            key="SIGNUP_RATE_LIMIT_PER_HOUR",
            prompt="Signup attempts per hour (per IP)",
            default=context.current("SIGNUP_RATE_LIMIT_PER_HOUR") or "20",
            required=True,
        ),
        field="SIGNUP_RATE_LIMIT_PER_HOUR",
        minimum=1,
    )
    context.set_backend("SIGNUP_RATE_LIMIT_PER_HOUR", str(rate_limit))

    plan_code = provider.prompt_string(
        key="SIGNUP_DEFAULT_PLAN_CODE",
        prompt="Default signup plan code",
        default=context.current("SIGNUP_DEFAULT_PLAN_CODE") or "starter",
        required=True,
    )
    context.set_backend("SIGNUP_DEFAULT_PLAN_CODE", plan_code)

    trial_days = parse_positive_int(
        provider.prompt_string(
            key="SIGNUP_DEFAULT_TRIAL_DAYS",
            prompt="Default trial days",
            default=context.current("SIGNUP_DEFAULT_TRIAL_DAYS") or "14",
            required=True,
        ),
        field="SIGNUP_DEFAULT_TRIAL_DAYS",
        minimum=1,
    )
    context.set_backend("SIGNUP_DEFAULT_TRIAL_DAYS", str(trial_days))

    run_retry_here = provider.prompt_bool(
        key="ENABLE_BILLING_RETRY_WORKER",
        prompt="Run the Stripe retry worker inside this deployment?",
        default=context.current_bool("ENABLE_BILLING_RETRY_WORKER", True),
    )
    context.set_backend_bool("ENABLE_BILLING_RETRY_WORKER", run_retry_here)
    deployment_mode = "inline" if run_retry_here else "dedicated"
    context.set_backend("BILLING_RETRY_DEPLOYMENT_MODE", deployment_mode)

    replay_stream = provider.prompt_bool(
        key="ENABLE_BILLING_STREAM_REPLAY",
        prompt="Replay Stripe events from Redis on startup?",
        default=context.current_bool("ENABLE_BILLING_STREAM_REPLAY", True),
    )
    context.set_backend_bool("ENABLE_BILLING_STREAM_REPLAY", replay_stream)
