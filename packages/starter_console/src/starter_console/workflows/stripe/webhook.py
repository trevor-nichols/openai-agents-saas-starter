from __future__ import annotations

import os
from dataclasses import dataclass

from starter_console.adapters.env import EnvFile
from starter_console.adapters.stripe_cli import StripeCli
from starter_console.core import CLIContext, CLIError

from .cli_helpers import ensure_stripe_cli


@dataclass(slots=True)
class WebhookSecretConfig:
    forward_url: str
    print_only: bool
    skip_stripe_cli: bool


def run_webhook_secret(ctx: CLIContext, config: WebhookSecretConfig) -> str:
    if ctx.presenter is None:  # pragma: no cover - defensive
        raise CLIError("Presenter not initialized.")
    stripe_cli = StripeCli()
    if not config.skip_stripe_cli:
        ensure_stripe_cli(
            cli=stripe_cli,
            console=ctx.console,
            prompt=ctx.presenter.prompt,
            non_interactive=False,
        )

    ctx.console.info(
        f"Requesting webhook secret via Stripe CLI (forward -> {config.forward_url})",
        topic="stripe",
    )
    secret = stripe_cli.capture_webhook_secret(config.forward_url)

    if config.print_only:
        ctx.console.info("Webhook signing secret (not saved):", topic="stripe")
        ctx.console.print(secret)
        return secret

    env_local = EnvFile(ctx.project_root / "apps" / "api-service" / ".env.local")
    env_local.set("STRIPE_WEBHOOK_SECRET", secret)
    env_local.save()
    os.environ["STRIPE_WEBHOOK_SECRET"] = secret
    ctx.console.success(
        f"Saved STRIPE_WEBHOOK_SECRET={_mask(secret)} to apps/api-service/.env.local",
        topic="stripe",
    )
    return secret


def _mask(value: str | None) -> str:
    if not value:
        return "(empty)"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


__all__ = ["WebhookSecretConfig", "run_webhook_secret"]
