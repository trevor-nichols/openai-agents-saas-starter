from __future__ import annotations

from dataclasses import dataclass

from starter_cli.adapters.env import EnvFile, aggregate_env_values
from starter_cli.core import CLIContext

REQUIRED_ENV_KEYS = ("STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "STRIPE_PRODUCT_PRICE_MAP")


@dataclass(frozen=True, slots=True)
class StripeStatus:
    values: dict[str, str | None]
    enable_billing: str


def load_stripe_status(ctx: CLIContext) -> StripeStatus:
    env_path = ctx.project_root / "apps" / "api-service" / ".env.local"
    env_files = [EnvFile(env_path)] if env_path.exists() else []
    values = aggregate_env_values(env_files, REQUIRED_ENV_KEYS)
    import os

    enable_billing = os.environ.get("ENABLE_BILLING") or ""
    return StripeStatus(values=values, enable_billing=enable_billing)


__all__ = ["REQUIRED_ENV_KEYS", "StripeStatus", "load_stripe_status"]
