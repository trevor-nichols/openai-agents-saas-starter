from __future__ import annotations

import json
import os
import signal
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from types import FrameType

from starter_console.adapters.env import (
    aggregate_env_values,
    build_env_scope,
    expand_env_placeholders,
)
from starter_console.adapters.stripe_cli import StripeCli
from starter_console.adapters.stripe_sdk import build_stripe_client, require_stripe_sdk
from starter_console.core import CLIContext, CLIError
from starter_console.ports.presentation import PromptPort
from starter_console.services.stripe import (
    PLAN_CATALOG,
    parse_amount_cents,
    parse_plan_overrides,
)
from starter_console.services.stripe.env import (
    load_backend_env_files,
    update_backend_env,
)
from starter_console.services.stripe.provisioner import StripeProvisioner

from .cli_helpers import ensure_stripe_cli
from .constants import AGGREGATED_KEYS


@dataclass(slots=True)
class StripeSetupConfig:
    currency: str
    trial_days: int
    non_interactive: bool
    secret_key: str | None
    webhook_secret: str | None
    auto_webhook_secret: bool
    webhook_forward_url: str
    plan_overrides: Iterable[str]
    skip_postgres: bool
    skip_stripe_cli: bool


@dataclass(slots=True)
class StripeSetupResult:
    price_map: dict[str, str]
    secret_key: str
    webhook_secret: str


def run_stripe_setup(ctx: CLIContext, config: StripeSetupConfig) -> StripeSetupResult:
    require_stripe_sdk()
    _install_signal_handlers(ctx)

    if ctx.presenter is None:  # pragma: no cover - defensive
        raise CLIError("Presenter not initialized.")
    prompt = ctx.presenter.prompt

    env_files = load_backend_env_files(ctx.project_root)
    aggregated = aggregate_env_values(env_files, AGGREGATED_KEYS)
    env_scope = build_env_scope(env_files)

    stripe_cli = StripeCli()
    if not config.skip_stripe_cli and not config.non_interactive:
        ensure_stripe_cli(
            cli=stripe_cli,
            console=ctx.console,
            prompt=prompt,
            non_interactive=config.non_interactive,
        )

    if not config.skip_postgres:
        _maybe_prepare_postgres(ctx, prompt, aggregated, env_scope, config.non_interactive)

    secret_key = _obtain_secret(
        prompt,
        label="Stripe secret key",
        existing=aggregated.get("STRIPE_SECRET_KEY"),
        provided=config.secret_key,
        non_interactive=config.non_interactive,
    )
    webhook_secret = _collect_webhook_secret(
        prompt,
        ctx=ctx,
        existing=aggregated.get("STRIPE_WEBHOOK_SECRET"),
        config=config,
        stripe_cli=stripe_cli,
    )

    plan_amounts = _resolve_plan_amounts(ctx, prompt, config)
    ctx.console.info("Provisioning Stripe products/prices...", topic="stripe")
    client = build_stripe_client(api_key=secret_key)
    provisioner = StripeProvisioner(
        client=client,
        currency=config.currency,
        trial_days=config.trial_days,
    )
    result = provisioner.provision(plan_amounts)

    for plan in result.plans:
        ctx.console.success(
            f"Configured {plan.name} "
            f"({config.currency.upper()} {plan.amount_cents / 100:.2f}) -> {plan.price_id}",
            topic="stripe",
        )

    update_backend_env(
        env_files[0],
        secret_key=secret_key,
        webhook_secret=webhook_secret,
        price_map=result.price_map,
    )

    ctx.console.success(
        "Stripe configuration captured in apps/api-service/.env.local",
        topic="stripe",
    )
    summary = json.dumps(
        {
            "STRIPE_SECRET_KEY": _mask(secret_key),
            "STRIPE_WEBHOOK_SECRET": _mask(webhook_secret),
            "STRIPE_PRODUCT_PRICE_MAP": result.price_map,
            "ENABLE_BILLING": True,
        },
        indent=2,
    )
    ctx.console.info("Summary:", topic="stripe")
    ctx.console.print(summary)

    return StripeSetupResult(
        price_map=result.price_map,
        secret_key=secret_key,
        webhook_secret=webhook_secret,
    )


def _install_signal_handlers(ctx: CLIContext) -> None:
    def _graceful_exit(signum: int, _frame: FrameType | None) -> None:
        ctx.console.warn(f"Received signal {signum}. Exiting.")
        raise SystemExit(1)

    signal.signal(signal.SIGINT, _graceful_exit)
    signal.signal(signal.SIGTERM, _graceful_exit)


def _maybe_prepare_postgres(
    ctx: CLIContext,
    prompt: PromptPort,
    aggregated: dict[str, str | None],
    env_scope: dict[str, str],
    non_interactive: bool,
) -> None:
    database_url = (
        aggregated.get("DATABASE_URL")
        or env_scope.get("DATABASE_URL")
        or os.environ.get("DATABASE_URL")
    )
    if non_interactive:
        return
    ctx.console.info("Postgres helper", topic="postgres")
    if prompt.prompt_bool(
        key="stripe_postgres_start",
        prompt="Start or refresh the local Postgres stack via `just dev-up`?",
        default=True,
    ):
        try:
            _run_interactive(ctx, ["just", "dev-up"])
        except (FileNotFoundError, OSError, subprocess.CalledProcessError) as exc:
            ctx.console.warn(
                f"`just dev-up` failed ({exc}). Fix Postgres manually.",
                topic="postgres",
            )

    if not database_url:
        database_url = prompt.prompt_string(
            key="stripe_database_url",
            prompt="Enter DATABASE_URL (leave blank to skip)",
            default="",
            required=False,
        )
    if database_url and prompt.prompt_bool(
        key="stripe_postgres_psql",
        prompt="Attempt a psql connection test?",
        default=False,
    ):
        expanded = expand_env_placeholders(database_url, env_scope)
        normalized = expanded.replace("postgresql+asyncpg", "postgresql").replace(
            "postgresql", "postgres", 1
        )
        try:
            _run_command(["psql", normalized, "-c", "\\q"], check=True)
            ctx.console.success("psql connectivity verified.", topic="postgres")
        except (FileNotFoundError, OSError, subprocess.CalledProcessError):
            ctx.console.warn(
                "psql test failed. Ensure Postgres is reachable.",
                topic="postgres",
            )


def _collect_webhook_secret(
    prompt: PromptPort,
    *,
    ctx: CLIContext,
    existing: str | None,
    config: StripeSetupConfig,
    stripe_cli: StripeCli,
) -> str:
    if config.webhook_secret:
        return config.webhook_secret

    if config.non_interactive:
        return _obtain_secret(
            prompt=prompt,
            label="Stripe webhook secret",
            existing=existing,
            provided=config.webhook_secret,
            non_interactive=True,
        )

    if existing and prompt.prompt_bool(
        key="stripe_webhook_reuse",
        prompt=f"Reuse existing webhook secret {_mask(existing)}?",
        default=True,
    ):
        return existing

    if config.auto_webhook_secret or prompt.prompt_bool(
        key="stripe_webhook_auto",
        prompt="Generate a webhook signing secret via Stripe CLI now?",
        default=True,
    ):
        ctx.console.info(
            f"Requesting webhook secret via Stripe CLI (forward -> {config.webhook_forward_url})",
            topic="stripe",
        )
        return stripe_cli.capture_webhook_secret(config.webhook_forward_url)

    return _obtain_secret(
        prompt=prompt,
        label="Stripe webhook secret",
        existing=existing,
        provided=None,
        non_interactive=False,
    )


def _obtain_secret(
    prompt: PromptPort,
    *,
    label: str,
    existing: str | None,
    provided: str | None,
    non_interactive: bool,
) -> str:
    if non_interactive:
        if not provided:
            raise CLIError(f"{label} is required for --non-interactive runs.")
        return provided

    return prompt.prompt_secret(
        key=f"stripe_{label.lower().replace(' ', '_')}",
        prompt=label,
        existing=existing,
        required=existing is None,
    )


def _resolve_plan_amounts(
    ctx: CLIContext,
    prompt: PromptPort,
    config: StripeSetupConfig,
) -> dict[str, int]:
    overrides = parse_plan_overrides(
        config.plan_overrides,
        require_all=config.non_interactive,
    )
    plan_amounts: dict[str, int] = {}
    for plan in PLAN_CATALOG:
        if plan.code in overrides:
            plan_amounts[plan.code] = overrides[plan.code]
            continue
        if config.non_interactive:
            plan_amounts[plan.code] = plan.default_cents
            continue
        default_display = f"{Decimal(plan.default_cents) / Decimal(100):.2f}"
        while True:
            raw = prompt.prompt_string(
                key=f"stripe_plan_{plan.code}",
                prompt=(
                    f"Monthly price for {plan.name} in {config.currency.upper()} "
                    f"(default {default_display})"
                ),
                default=default_display,
                required=True,
            )
            try:
                plan_amounts[plan.code] = parse_amount_cents(raw)
                break
            except CLIError as exc:
                ctx.console.warn(str(exc), topic="stripe")
    return plan_amounts


def _run_command(
    cmd: list[str], *, check: bool = True, capture_output: bool = False
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=check,
        text=True,
        capture_output=capture_output,
    )


def _run_interactive(ctx: CLIContext, cmd: list[str]) -> None:
    ctx.console.info(" ".join(cmd), topic="exec")
    _run_command(cmd, check=True)


def _mask(value: str | None) -> str:
    if not value:
        return "(empty)"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


__all__ = ["StripeSetupConfig", "StripeSetupResult", "run_stripe_setup"]
