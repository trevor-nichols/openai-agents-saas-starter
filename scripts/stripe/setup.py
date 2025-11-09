#!/usr/bin/env python3
"""Stripe onboarding helper for the anything-agents starter."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, Iterable
import re

try:
    import stripe  # type: ignore
except ImportError as exc:  # pragma: no cover - executed before tests
    print(
        "[ERROR] Missing dependency 'stripe'. Install with `pip install 'anything-agents[dev]'`",
        file=sys.stderr,
    )
    raise SystemExit(1) from exc


REQUIRED_ENV_KEYS = ("STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "STRIPE_PRODUCT_PRICE_MAP")
AGGREGATED_KEYS = (*REQUIRED_ENV_KEYS, "DATABASE_URL")

PLAN_CATALOG = (
    {"code": "starter", "name": "Starter", "default_cents": 2000},
    {"code": "pro", "name": "Pro", "default_cents": 9900},
)
TRIAL_DAYS = 7
DEFAULT_CURRENCY = "usd"
PLAN_METADATA_KEY = "anything_agents_plan_code"


class Logger:
    def info(self, message: str, scope: str | None = None) -> None:
        self._emit("INFO", message, scope)

    def warn(self, message: str, scope: str | None = None) -> None:
        self._emit("WARN", message, scope)

    def error(self, message: str, scope: str | None = None) -> None:
        self._emit("ERROR", message, scope)

    def success(self, message: str, scope: str | None = None) -> None:
        self._emit("SUCCESS", message, scope)

    def _emit(self, level: str, message: str, scope: str | None) -> None:
        prefix = f"[{level}]"
        if scope:
            prefix = f"{prefix} [{scope}]"
        print(f"{prefix} {message}")


LOGGER = Logger()


class EnvFile:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.lines: list[str] = []
        if path.exists():
            self.lines = path.read_text(encoding="utf-8").splitlines()
        self._index: Dict[str, int] = {}
        self._dirty = False
        self._reindex()

    def _reindex(self) -> None:
        self._index.clear()
        for idx, line in enumerate(self.lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue
            key, _ = stripped.split("=", 1)
            key = key.strip()
            if key:
                self._index[key] = idx

    def get(self, key: str) -> str | None:
        idx = self._index.get(key)
        if idx is None:
            return None
        _, value = self._split_line(self.lines[idx])
        return value

    def set(self, key: str, value: str) -> None:
        serialized = self._serialize_value(value)
        idx = self._index.get(key)
        if idx is None:
            self.lines.append(f"{key}={serialized}")
            self._index[key] = len(self.lines) - 1
        else:
            self.lines[idx] = f"{key}={serialized}"
        self._dirty = True

    def save(self) -> None:
        if not self._dirty:
            return
        body = "\n".join(self.lines)
        if not body.endswith("\n"):
            body += "\n"
        self.path.write_text(body, encoding="utf-8")
        self._dirty = False

    def as_dict(self) -> dict[str, str]:
        data: dict[str, str] = {}
        for key in self._index:
            data[key] = self.get(key) or ""
        return data

    @staticmethod
    def _split_line(line: str) -> tuple[str, str]:
        if "=" not in line:
            return line, ""
        key, value = line.split("=", 1)
        return key.strip(), EnvFile._unquote(value.strip())

    @staticmethod
    def _unquote(value: str) -> str:
        if not value:
            return ""
        if (value.startswith("\"") and value.endswith("\"")) or (
            value.startswith("'") and value.endswith("'")
        ):
            return value[1:-1]
        if value.startswith("\"\"") and value.endswith("\"\""):
            return value[3:-3]
        if " #" in value:
            value = value.split(" #", 1)[0]
        return value.strip()

    @staticmethod
    def _serialize_value(value: str) -> str:
        if value == "":
            return '""'
        safe = all(ch.isalnum() or ch in "_.:@/-" for ch in value)
        return value if safe else json.dumps(value)


def run_command(cmd: list[str], *, check: bool = True, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=check,
        text=True,
        capture_output=capture_output,
    )


def ensure_stripe_cli() -> None:
    LOGGER.info("Checking Stripe CLI installation...", "stripe")
    try:
        result = run_command(["stripe", "--version"], capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        LOGGER.error(
            "Stripe CLI not found. Install from https://docs.stripe.com/stripe-cli and rerun.",
            "stripe",
        )
        raise SystemExit(1)
    LOGGER.success(result.stdout.strip(), "stripe")
    try:
        run_command(["stripe", "config", "--list"], capture_output=True)
        LOGGER.success("Stripe CLI authentication verified.", "stripe")
    except subprocess.CalledProcessError:
        LOGGER.warn("Stripe CLI is not authenticated.", "stripe")
        if prompt_yes_no("Open the Stripe CLI auth page?", default=False):
            open_url("https://dashboard.stripe.com/stripe-cli/auth")
        if prompt_yes_no("Run `stripe login --interactive` now?", default=True):
            run_interactive(["stripe", "login", "--interactive"])
            run_command(["stripe", "config", "--list"], capture_output=True)
            LOGGER.success("Stripe CLI authentication confirmed.", "stripe")
        else:
            LOGGER.error("Cannot continue without Stripe CLI authentication.", "stripe")
            raise SystemExit(1)


def open_url(url: str) -> None:
    opener = "open" if sys.platform == "darwin" else "start" if os.name == "nt" else "xdg-open"
    try:
        subprocess.Popen([opener, url])  # noqa: S603 - user initiated
        LOGGER.info(f"Opened {url} in your browser.")
    except OSError:
        LOGGER.warn(f"Unable to open {url}. Please visit it manually.")


def run_interactive(cmd: list[str]) -> None:
    LOGGER.info(" ".join(cmd), "exec")
    subprocess.run(cmd, check=True)


def maybe_prepare_postgres(env_values: dict[str, str | None], env_scope: dict[str, str]) -> None:
    LOGGER.info("Postgres helper", "postgres")
    if prompt_yes_no("Start or refresh the local Postgres stack via `make dev-up`?", default=True):
        try:
            run_interactive(["make", "dev-up"])
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            LOGGER.warn(f"make dev-up failed ({exc}). Continue after fixing Postgres manually.", "postgres")

    database_url = env_values.get("DATABASE_URL") or env_scope.get("DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not database_url:
        database_url = prompt_input("Enter DATABASE_URL (leave blank to skip)")
    if database_url and prompt_yes_no("Attempt a psql connection test?", default=False):
        expanded = expand_env_placeholders(database_url, env_scope)
        normalized = expanded.replace("postgresql+asyncpg", "postgresql").replace("postgresql", "postgres", 1)
        try:
            run_command(["psql", normalized, "-c", "\\q"], check=True)
            LOGGER.success("psql connectivity verified.", "postgres")
        except (FileNotFoundError, subprocess.CalledProcessError):
            LOGGER.warn("psql test failed. Ensure Postgres is reachable before enabling billing.", "postgres")


def prompt_secret(prompt_label: str, existing: str | None) -> str:
    while True:
        suffix = f" (leave blank to keep {mask(existing)})" if existing else ""
        value = input(f"{prompt_label}:{suffix} ").strip()
        if not value and existing:
            LOGGER.info("Keeping existing value.")
            return existing
        if value:
            return value
        LOGGER.warn("Value cannot be empty.")


def prompt_plan_amount(plan_name: str, default_cents: int, currency: str) -> int:
    default_display = f"{Decimal(default_cents) / Decimal(100):.2f}"
    while True:
        raw = input(
            f"Monthly price for {plan_name} in {currency.upper()} (default {default_display}): "
        ).strip()
        if not raw:
            return default_cents
        try:
            amount = Decimal(raw)
        except InvalidOperation:
            LOGGER.warn("Enter a numeric amount (e.g., 29 or 29.99).")
            continue
        if amount <= 0:
            LOGGER.warn("Amount must be greater than zero.")
            continue
        cents = int((amount * 100).to_integral_value())
        return cents


def provision_plans(
    *,
    api_key: str,
    plan_amounts: dict[str, int],
    currency: str,
) -> dict[str, str]:
    stripe.api_key = api_key
    price_map: dict[str, str] = {}
    for plan in PLAN_CATALOG:
        code = plan["code"]
        amount = plan_amounts[code]
        product = ensure_product(code=code, name=plan["name"])
        price = ensure_price(product_id=product.id, plan_code=code, amount_cents=amount, currency=currency)
        price_map[code] = price.id
        LOGGER.success(
            f"Configured {plan['name']} ({currency.upper()} {amount / 100:.2f}) → {price.id}",
            "stripe",
        )
    return price_map


def ensure_product(*, code: str, name: str):
    search_query = f"metadata['{PLAN_METADATA_KEY}']:'{code}'"
    products = stripe.Product.search(query=search_query, limit=1)
    if products.data:
        product = products.data[0]
        if product.name != name:
            stripe.Product.modify(product.id, name=name)
        return product
    return stripe.Product.create(name=name, metadata={PLAN_METADATA_KEY: code})


def ensure_price(*, product_id: str, plan_code: str, amount_cents: int, currency: str):
    prices = stripe.Price.list(product=product_id, active=True, limit=100)
    for price in prices.auto_paging_iter():  # type: ignore[attr-defined]
        recurring = getattr(price, "recurring", None)
        if not recurring:
            continue
        interval = recurring.get("interval")
        trial_days = recurring.get("trial_period_days")
        if (
            price.currency == currency
            and price.unit_amount == amount_cents
            and interval == "month"
            and trial_days == TRIAL_DAYS
        ):
            return price
    return stripe.Price.create(
        product=product_id,
        currency=currency,
        unit_amount=amount_cents,
        nickname=f"{plan_code.title()} Monthly",
        recurring={"interval": "month", "trial_period_days": TRIAL_DAYS},
        metadata={PLAN_METADATA_KEY: plan_code},
    )


def prompt_yes_no(question: str, *, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        answer = input(f"{question} ({hint}) ").strip().lower()
        if not answer:
            return default
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        LOGGER.warn("Please answer yes or no.")


def prompt_input(question: str) -> str:
    return input(f"{question}: ").strip()


def mask(value: str | None) -> str:
    if not value:
        return "(empty)"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}…{value[-4:]}"


def aggregate_env_values(files: Iterable[EnvFile]) -> dict[str, str | None]:
    aggregated: dict[str, str | None] = {key: None for key in AGGREGATED_KEYS}
    for file in files:
        for key in AGGREGATED_KEYS:
            if aggregated[key]:
                continue
            aggregated[key] = file.get(key)
    for key in AGGREGATED_KEYS:
        if aggregated[key]:
            continue
        aggregated[key] = os.environ.get(key)
    return aggregated


def build_env_scope(files: Iterable[EnvFile]) -> dict[str, str]:
    scope: dict[str, str] = {}
    for file in files:
        scope.update(file.as_dict())
    for key, value in os.environ.items():
        scope.setdefault(key, value)
    return scope


ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def expand_env_placeholders(value: str, scope: dict[str, str]) -> str:
    def replacer(match: re.Match[str]) -> str:
        key = match.group(1)
        return scope.get(key) or os.environ.get(key) or match.group(0)

    return ENV_PATTERN.sub(replacer, value)


def update_env_files(env_local: EnvFile, *, price_map: dict[str, str], secret: str, webhook: str) -> None:
    env_local.set("STRIPE_SECRET_KEY", secret)
    env_local.set("STRIPE_WEBHOOK_SECRET", webhook)
    env_local.set("STRIPE_PRODUCT_PRICE_MAP", json.dumps(price_map, separators=(",", ":")))
    env_local.set("ENABLE_BILLING", "true")
    env_local.save()


def graceful_exit(signum, _frame):  # type: ignore[override]
    LOGGER.warn(f"Received signal {signum}. Exiting.")
    raise SystemExit(1)


def main() -> None:
    signal.signal(signal.SIGINT, graceful_exit)
    signal.signal(signal.SIGTERM, graceful_exit)

    LOGGER.info("Stripe SaaS setup assistant starting…")
    ensure_stripe_cli()

    env_local = EnvFile(Path(".env.local"))
    env_fallback = EnvFile(Path(".env"))
    env_compose = EnvFile(Path(".env.compose"))
    aggregated = aggregate_env_values((env_local, env_fallback, env_compose))
    env_scope = build_env_scope((env_local, env_fallback, env_compose))

    maybe_prepare_postgres(aggregated, env_scope)

    secret_key = prompt_secret("Stripe secret key", aggregated.get("STRIPE_SECRET_KEY"))
    webhook_secret = prompt_secret("Stripe webhook secret", aggregated.get("STRIPE_WEBHOOK_SECRET"))

    plan_amounts: dict[str, int] = {}
    for plan in PLAN_CATALOG:
        cents = prompt_plan_amount(plan["name"], plan["default_cents"], DEFAULT_CURRENCY)
        plan_amounts[plan["code"]] = cents

    LOGGER.info("Provisioning Stripe products/prices…", "stripe")
    try:
        price_map = provision_plans(api_key=secret_key, plan_amounts=plan_amounts, currency=DEFAULT_CURRENCY)
    except stripe.error.StripeError as exc:  # type: ignore[attr-defined]
        LOGGER.error(f"Stripe API error: {exc.user_message or exc}", "stripe")
        raise SystemExit(1) from exc

    update_env_files(env_local, price_map=price_map, secret=secret_key, webhook=webhook_secret)

    LOGGER.success("Stripe configuration captured in .env.local")
    summary = json.dumps(
        {
            "STRIPE_SECRET_KEY": mask(secret_key),
            "STRIPE_WEBHOOK_SECRET": mask(webhook_secret),
            "STRIPE_PRODUCT_PRICE_MAP": price_map,
            "ENABLE_BILLING": True,
        },
        indent=2,
    )
    LOGGER.info("Summary:")
    print(summary)


if __name__ == "__main__":
    main()
