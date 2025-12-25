from __future__ import annotations

import os
from dataclasses import dataclass

from starter_cli.adapters.env import EnvFile, aggregate_env_values
from starter_cli.core import CLIContext
from starter_cli.core.constants import DEFAULT_ENV_FILES

REQUIRED_ENV_KEYS = ("STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "STRIPE_PRODUCT_PRICE_MAP")


@dataclass(frozen=True, slots=True)
class StripeStatus:
    values: dict[str, str | None]
    enable_billing: str


def load_stripe_status(ctx: CLIContext) -> StripeStatus:
    env_paths = list(ctx.loaded_env_files) or list(ctx.env_files)
    if ctx.skip_env:
        env_paths = [path for path in env_paths if path not in DEFAULT_ENV_FILES]
    env_files = [EnvFile(path) for path in env_paths if path.exists()]
    values = aggregate_env_values(env_files, REQUIRED_ENV_KEYS)
    enable_billing = os.environ.get("ENABLE_BILLING") or ""
    return StripeStatus(values=values, enable_billing=enable_billing)


__all__ = ["REQUIRED_ENV_KEYS", "StripeStatus", "load_stripe_status"]
