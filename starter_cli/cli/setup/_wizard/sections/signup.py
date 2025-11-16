from __future__ import annotations

from typing import Final

from starter_cli.cli.common import CLIError
from starter_cli.cli.console import console
from starter_cli.cli.setup._wizard.context import WizardContext
from starter_cli.cli.setup.inputs import HeadlessInputProvider, InputProvider
from starter_cli.cli.setup.validators import parse_positive_int

_SIGNUP_POLICY_DESCRIPTIONS: Final[dict[str, str]] = {
    "public": "Public signup enabled - anyone can self-register.",
    "invite_only": "Invite-only - require invite tokens before tenant creation.",
    "approval": "Approval required - collect requests and approve before issuing invites.",
}
_SIGNUP_POLICY_CHOICES: Final[set[str]] = set(_SIGNUP_POLICY_DESCRIPTIONS.keys())


def run(context: WizardContext, provider: InputProvider) -> None:
    console.info("[M4] Signup & Worker policy", topic="wizard")
    policy = _prompt_signup_policy(context, provider)
    context.set_backend("SIGNUP_ACCESS_POLICY", policy)
    context.set_backend_bool("ALLOW_PUBLIC_SIGNUP", policy == "public")

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


def _prompt_signup_policy(context: WizardContext, provider: InputProvider) -> str:
    default_policy = _resolve_policy_default(context, provider)
    choices_hint = "/".join(sorted(_SIGNUP_POLICY_CHOICES))
    while True:
        value = (
            provider.prompt_string(
                key="SIGNUP_ACCESS_POLICY",
                prompt=f"Signup exposure policy ({choices_hint})",
                default=default_policy,
                required=True,
            )
            .strip()
            .lower()
        )
        if value in _SIGNUP_POLICY_CHOICES:
            console.info(_SIGNUP_POLICY_DESCRIPTIONS[value], topic="wizard")
            return value
        if isinstance(provider, HeadlessInputProvider):
            raise CLIError(
                "SIGNUP_ACCESS_POLICY must be one of "
                f"{', '.join(sorted(_SIGNUP_POLICY_CHOICES))}."
            )
        console.warn(
            f"Value must be one of {', '.join(sorted(_SIGNUP_POLICY_CHOICES))}.",
            topic="wizard",
        )


def _resolve_policy_default(context: WizardContext, provider: InputProvider) -> str:
    existing = _normalize_policy(context.current("SIGNUP_ACCESS_POLICY"))
    if existing:
        return existing

    headless_policy = _normalize_policy(_headless_answer(provider, "SIGNUP_ACCESS_POLICY"))
    if headless_policy:
        return headless_policy

    headless_allow = _headless_answer(provider, "ALLOW_PUBLIC_SIGNUP")
    if headless_allow is not None:
        return "public" if _coerce_bool_like(headless_allow) else "invite_only"

    env_allow_value = context.current("ALLOW_PUBLIC_SIGNUP")
    if env_allow_value is not None:
        return "public" if _coerce_bool_like(env_allow_value) else "invite_only"

    return "invite_only"


def _normalize_policy(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    if normalized in _SIGNUP_POLICY_CHOICES:
        return normalized
    return None


def _headless_answer(provider: InputProvider, key: str) -> str | None:
    if isinstance(provider, HeadlessInputProvider):
        return provider.answers.get(key.upper())
    return None


def _coerce_bool_like(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y"}
