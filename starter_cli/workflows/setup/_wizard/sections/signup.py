from __future__ import annotations

from datetime import UTC, datetime
from typing import Final

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIError

from ...inputs import InputProvider, is_headless_provider
from ...validators import parse_non_negative_int, parse_positive_int
from ..context import WizardContext

_SIGNUP_POLICY_DESCRIPTIONS: Final[dict[str, str]] = {
    "public": "Public signup enabled - anyone can self-register.",
    "invite_only": "Invite-only - require invite tokens before tenant creation.",
    "approval": "Approval required - collect requests and approve before issuing invites.",
}
_SIGNUP_POLICY_CHOICES: Final[set[str]] = set(_SIGNUP_POLICY_DESCRIPTIONS.keys())


def run(context: WizardContext, provider: InputProvider) -> None:
    console.section(
        "Signup & Worker Policies",
        "Choose how tenants onboard and how the billing worker behaves by default.",
    )
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

    per_day_limit = parse_non_negative_int(
        provider.prompt_string(
            key="SIGNUP_RATE_LIMIT_PER_IP_DAY",
            prompt="Signup attempts per day (per IP)",
            default=context.current("SIGNUP_RATE_LIMIT_PER_IP_DAY") or "100",
            required=True,
        ),
        field="SIGNUP_RATE_LIMIT_PER_IP_DAY",
    )
    context.set_backend("SIGNUP_RATE_LIMIT_PER_IP_DAY", str(per_day_limit))

    per_email_limit = parse_non_negative_int(
        provider.prompt_string(
            key="SIGNUP_RATE_LIMIT_PER_EMAIL_DAY",
            prompt="Signup attempts per day (per email)",
            default=context.current("SIGNUP_RATE_LIMIT_PER_EMAIL_DAY") or "3",
            required=True,
        ),
        field="SIGNUP_RATE_LIMIT_PER_EMAIL_DAY",
    )
    context.set_backend("SIGNUP_RATE_LIMIT_PER_EMAIL_DAY", str(per_email_limit))

    per_domain_limit = parse_non_negative_int(
        provider.prompt_string(
            key="SIGNUP_RATE_LIMIT_PER_DOMAIN_DAY",
            prompt="Signup attempts per day (per domain)",
            default=context.current("SIGNUP_RATE_LIMIT_PER_DOMAIN_DAY") or "20",
            required=True,
        ),
        field="SIGNUP_RATE_LIMIT_PER_DOMAIN_DAY",
    )
    context.set_backend("SIGNUP_RATE_LIMIT_PER_DOMAIN_DAY", str(per_domain_limit))

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

    concurrent_limit = parse_non_negative_int(
        provider.prompt_string(
            key="SIGNUP_CONCURRENT_REQUESTS_LIMIT",
            prompt="Pending signup requests allowed per IP",
            default=context.current("SIGNUP_CONCURRENT_REQUESTS_LIMIT") or "3",
            required=True,
        ),
        field="SIGNUP_CONCURRENT_REQUESTS_LIMIT",
    )
    context.set_backend("SIGNUP_CONCURRENT_REQUESTS_LIMIT", str(concurrent_limit))

    worker_mode = _prompt_worker_mode(context, provider)
    run_retry_here = worker_mode == "inline"
    context.set_backend_bool("ENABLE_BILLING_RETRY_WORKER", run_retry_here)
    context.set_backend("BILLING_RETRY_DEPLOYMENT_MODE", worker_mode)

    if run_retry_here:
        replay_stream = provider.prompt_bool(
            key="ENABLE_BILLING_STREAM_REPLAY",
            prompt="Replay Stripe events from Redis on startup?",
            default=context.current_bool("ENABLE_BILLING_STREAM_REPLAY", True),
        )
        context.set_backend_bool("ENABLE_BILLING_STREAM_REPLAY", replay_stream)
    else:
        context.set_backend_bool("ENABLE_BILLING_STREAM_REPLAY", False)
        console.info(
            "Disabling billing stream replay in this env (dedicated worker will own it).",
            topic="wizard",
        )

    _write_worker_guidance(context, worker_mode)


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
        if is_headless_provider(provider):
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


def _prompt_worker_mode(context: WizardContext, provider: InputProvider) -> str:
    existing = _normalize_worker_mode(context.current("BILLING_RETRY_DEPLOYMENT_MODE"))
    headless_mode = _normalize_worker_mode(
        _headless_answer(provider, "BILLING_RETRY_DEPLOYMENT_MODE")
    )
    if headless_mode:
        return headless_mode

    is_headless = is_headless_provider(provider)
    if is_headless and not existing:
        raise CLIError(
            "Headless wizard runs must set BILLING_RETRY_DEPLOYMENT_MODE=inline|dedicated. "
            "Update your answers file before re-running."
        )

    default_mode = existing
    if not default_mode:
        default_mode = "inline" if context.profile == "local" else "dedicated"
    while True:
        value = (
            provider.prompt_string(
                key="BILLING_RETRY_DEPLOYMENT_MODE",
                prompt=(
                    "Stripe retry worker deployment mode "
                    "(inline runs inside this API pod, dedicated requires a separate worker)"
                ),
                default=default_mode,
                required=True,
            )
            .strip()
            .lower()
        )
        normalized = _normalize_worker_mode(value)
        if normalized:
            if normalized == "dedicated":
                console.info(
                    "CLI will disable the worker on this env and generate worker overrides.",
                    topic="wizard",
                )
            else:
                console.info(
                    "CLI will run the retry worker inside this deployment (single replica).",
                    topic="wizard",
                )
            return normalized
        if is_headless_provider(provider):
            raise CLIError("BILLING_RETRY_DEPLOYMENT_MODE must be 'inline' or 'dedicated'.")
        console.warn("Enter either 'inline' or 'dedicated'.", topic="wizard")


def _normalize_worker_mode(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    if normalized in {"inline", "dedicated"}:
        return normalized
    return None


def _write_worker_guidance(context: WizardContext, worker_mode: str) -> None:
    reports_dir = context.cli_ctx.project_root / "var/reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).isoformat()
    summary_path = reports_dir / "billing-worker-topology.md"
    overlay_path = reports_dir / "billing-worker.env"
    inline = worker_mode == "inline"
    lines = [
        "# Stripe Retry Worker Topology",
        "",
        f"- Generated: `{timestamp}`",
        f"- Profile: `{context.profile}`",
        f"- Mode: `{worker_mode}`",
    ]
    if inline:
        if overlay_path.exists():
            overlay_path.unlink()
            console.info(
                "Removed dedicated worker overrides (current mode is inline).",
                topic="wizard",
            )
        lines.extend(
            [
                "",
                "This environment runs exactly one FastAPI replica, so the retry worker stays "
                "inline. Deploying additional replicas requires switching to `dedicated` mode and "
                "re-running the wizard so only one pod keeps `ENABLE_BILLING_RETRY_WORKER=true`.",
            ]
        )
    else:
        overlay_lines = [
            "# Copy these overrides into the env for the single billing worker deployment.",
            "ENABLE_BILLING=true",
            "ENABLE_BILLING_RETRY_WORKER=true",
            "ENABLE_BILLING_STREAM_REPLAY=true",
            "BILLING_RETRY_DEPLOYMENT_MODE=dedicated",
        ]
        overlay_path.write_text("\n".join(overlay_lines) + "\n", encoding="utf-8")
        console.success(f"Billing worker overrides written to {overlay_path}", topic="wizard")
        lines.extend(
            [
                "",
                "Run a separate `billing-worker` deployment (replicas: 1) using the overrides "
                "written to `var/reports/billing-worker.env`. All customer-facing API pods must "
                "keep `ENABLE_BILLING_RETRY_WORKER=false` and "
                "`ENABLE_BILLING_STREAM_REPLAY=false`.",
                "Refer to docs/billing/stripe-runbook.md for the deployment matrix and monitoring "
                "checks (OPS-004).",
            ]
        )
    summary_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    console.success(f"Worker topology documented in {summary_path}", topic="wizard")


def _headless_answer(provider: InputProvider, key: str) -> str | None:
    answers = getattr(provider, "answers", None)
    if answers:
        return answers.get(key.upper())
    return None


def _coerce_bool_like(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y"}
