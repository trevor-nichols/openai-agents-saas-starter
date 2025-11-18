from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from types import FrameType
from typing import Any, TypedDict, cast

try:  # pragma: no cover - optional dependency
    import stripe as stripe_module
except ImportError:  # pragma: no cover - handled at runtime
    stripe: Any | None = None
else:
    stripe = cast(Any, stripe_module)

from starter_cli.adapters.env import (
    EnvFile,
    aggregate_env_values,
    build_env_scope,
    expand_env_placeholders,
)
from starter_cli.adapters.io.console import console
from starter_cli.core import CLIContext, CLIError

REQUIRED_ENV_KEYS = ("STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "STRIPE_PRODUCT_PRICE_MAP")
AGGREGATED_KEYS = (*REQUIRED_ENV_KEYS, "DATABASE_URL")


class PlanConfig(TypedDict):
    code: str
    name: str
    default_cents: int


PLAN_CATALOG: tuple[PlanConfig, ...] = (
    {"code": "starter", "name": "Starter", "default_cents": 2000},
    {"code": "pro", "name": "Pro", "default_cents": 9900},
)
PLAN_METADATA_KEY = "starter_cli_plan_code"


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    stripe_parser = subparsers.add_parser("stripe", help="Stripe provisioning helpers.")
    stripe_subparsers = stripe_parser.add_subparsers(dest="stripe_command")

    setup_parser = stripe_subparsers.add_parser(
        "setup",
        help="Interactive onboarding flow for billing assets and secrets.",
    )
    setup_parser.add_argument(
        "--currency",
        default="usd",
        help="Currency for plan provisioning (default: usd).",
    )
    setup_parser.add_argument(
        "--trial-days",
        type=int,
        default=7,
        help="Trial period in days for generated prices.",
    )
    setup_parser.add_argument(
        "--secret-key",
        help="Stripe secret key (sk_live_...). Required for --non-interactive.",
    )
    setup_parser.add_argument(
        "--webhook-secret",
        help="Stripe webhook signing secret. Required for --non-interactive.",
    )
    setup_parser.add_argument(
        "--plan",
        action="append",
        metavar="CODE=CENTS",
        help="Override plan pricing (e.g., starter=2500).",
    )
    setup_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Disable prompts and rely entirely on provided flags.",
    )
    setup_parser.add_argument(
        "--skip-postgres-check",
        action="store_true",
        help="Skip the optional Postgres helper/test.",
    )
    setup_parser.add_argument(
        "--skip-stripe-cli",
        action="store_true",
        help="Skip Stripe CLI verification (use when running in CI).",
    )
    setup_parser.set_defaults(handler=handle_stripe_setup)


def handle_stripe_setup(args: argparse.Namespace, ctx: CLIContext) -> int:
    flow = StripeSetupFlow(
        ctx=ctx,
        currency=args.currency,
        trial_days=args.trial_days,
        non_interactive=args.non_interactive,
        secret_key=args.secret_key,
        webhook_secret=args.webhook_secret,
        plan_overrides=args.plan or [],
        skip_postgres=args.skip_postgres_check,
        skip_stripe_cli=args.skip_stripe_cli,
    )
    flow.run()
    return 0


@dataclass(slots=True)
class StripeSetupFlow:
    ctx: CLIContext
    currency: str
    trial_days: int
    non_interactive: bool
    secret_key: str | None
    webhook_secret: str | None
    plan_overrides: Iterable[str]
    skip_postgres: bool
    skip_stripe_cli: bool

    def run(self) -> None:
        self._require_stripe_dependency()
        self._install_signal_handlers()
        env_files = self._load_env_files()
        aggregated = aggregate_env_values(env_files, AGGREGATED_KEYS)
        env_scope = build_env_scope(env_files)

        if not self.skip_stripe_cli and not self.non_interactive:
            self._ensure_stripe_cli()

        if not self.skip_postgres:
            self._maybe_prepare_postgres(aggregated, env_scope)

        secret_key = self._obtain_secret(
            "Stripe secret key",
            aggregated.get("STRIPE_SECRET_KEY"),
            provided=self.secret_key,
        )
        webhook_secret = self._obtain_secret(
            "Stripe webhook secret",
            aggregated.get("STRIPE_WEBHOOK_SECRET"),
            provided=self.webhook_secret,
        )

        plan_amounts = self._resolve_plan_amounts()
        console.info("Provisioning Stripe products/prices…", topic="stripe")
        price_map = self._provision_plans(secret_key, plan_amounts)
        self._update_env(env_files[0], price_map, secret_key, webhook_secret)

        console.success("Stripe configuration captured in .env.local", topic="stripe")
        summary = json.dumps(
            {
                "STRIPE_SECRET_KEY": self._mask(secret_key),
                "STRIPE_WEBHOOK_SECRET": self._mask(webhook_secret),
                "STRIPE_PRODUCT_PRICE_MAP": price_map,
                "ENABLE_BILLING": True,
            },
            indent=2,
        )
        console.info("Summary:", topic="stripe")
        print(summary)

    def _require_stripe_dependency(self) -> None:
        if stripe is None:  # pragma: no cover - runtime dependency
            raise CLIError(
                "Missing dependency 'stripe'. Install with `pip install 'anything-agents[dev]'`."
            )

    def _install_signal_handlers(self) -> None:
        signal.signal(signal.SIGINT, self._graceful_exit)
        signal.signal(signal.SIGTERM, self._graceful_exit)

    def _load_env_files(self) -> tuple[EnvFile, EnvFile, EnvFile]:
        env_local = EnvFile(self.ctx.project_root / ".env.local")
        env_fallback = EnvFile(self.ctx.project_root / ".env")
        env_compose = EnvFile(self.ctx.project_root / ".env.compose")
        return (env_local, env_fallback, env_compose)

    def _ensure_stripe_cli(self) -> None:
        console.info("Checking Stripe CLI installation…", topic="stripe")
        try:
            result = self._run_command(["stripe", "--version"], capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            raise CLIError(
                "Stripe CLI not found. Install from https://docs.stripe.com/stripe-cli."
            ) from exc
        console.success(result.stdout.strip(), topic="stripe")
        try:
            self._run_command(["stripe", "config", "--list"], capture_output=True)
            console.success("Stripe CLI authentication verified.", topic="stripe")
        except subprocess.CalledProcessError as exc:
            console.warn("Stripe CLI is not authenticated.", topic="stripe")
            if not self.non_interactive and self._prompt_yes_no(
                "Open the Stripe CLI auth page?", default=False
            ):
                self._open_url("https://dashboard.stripe.com/stripe-cli/auth")
            if not self.non_interactive and self._prompt_yes_no(
                "Run `stripe login --interactive` now?", default=True
            ):
                self._run_interactive(["stripe", "login", "--interactive"])
                self._run_command(["stripe", "config", "--list"], capture_output=True)
                console.success("Stripe CLI authentication confirmed.", topic="stripe")
            else:
                raise CLIError(
                    "Cannot continue without Stripe CLI authentication."
                ) from exc

    def _maybe_prepare_postgres(
        self,
        aggregated: dict[str, str | None],
        env_scope: dict[str, str],
    ) -> None:
        database_url = (
            aggregated.get("DATABASE_URL")
            or env_scope.get("DATABASE_URL")
            or os.environ.get("DATABASE_URL")
        )
        if self.non_interactive:
            return
        console.info("Postgres helper", topic="postgres")
        if self._prompt_yes_no("Start or refresh the local Postgres stack via `make dev-up`?"):
            try:
                self._run_interactive(["make", "dev-up"])
            except (FileNotFoundError, subprocess.CalledProcessError) as exc:
                console.warn(
                    f"`make dev-up` failed ({exc}). Fix Postgres manually.",
                    topic="postgres",
                )

        if not database_url:
            database_url = self._prompt_input("Enter DATABASE_URL (leave blank to skip)")
        if database_url and self._prompt_yes_no("Attempt a psql connection test?", default=False):
            expanded = expand_env_placeholders(database_url, env_scope)
            normalized = expanded.replace("postgresql+asyncpg", "postgresql").replace(
                "postgresql", "postgres", 1
            )
            try:
                self._run_command(["psql", normalized, "-c", "\\q"], check=True)
                console.success("psql connectivity verified.", topic="postgres")
            except (FileNotFoundError, subprocess.CalledProcessError):
                console.warn("psql test failed. Ensure Postgres is reachable.", topic="postgres")

    def _obtain_secret(self, label: str, existing: str | None, *, provided: str | None) -> str:
        if self.non_interactive:
            value = provided
            if not value:
                raise CLIError(f"{label} is required for --non-interactive runs.")
            return value

        while True:
            suffix = f" (leave blank to keep {self._mask(existing)})" if existing else ""
            value = input(f"{label}:{suffix} ").strip()
            if not value and existing:
                console.info("Keeping existing value.", topic="stripe")
                return existing
            if value:
                return value
            console.warn("Value cannot be empty.", topic="stripe")

    def _resolve_plan_amounts(self) -> dict[str, int]:
        overrides = self._parse_plan_overrides()
        plan_amounts: dict[str, int] = {}
        for plan in PLAN_CATALOG:
            code = plan["code"]
            if code in overrides:
                plan_amounts[code] = overrides[code]
            else:
                plan_amounts[code] = self._prompt_plan_amount(plan["name"], plan["default_cents"])
        return plan_amounts

    def _parse_plan_overrides(self) -> dict[str, int]:
        overrides: dict[str, int] = {}
        for item in self.plan_overrides:
            if "=" not in item:
                raise CLIError(f"Invalid plan override '{item}'. Expected format code=amount.")
            code, raw = item.split("=", 1)
            overrides[code.strip()] = self._parse_amount_cents(raw.strip())
        if self.non_interactive:
            missing = [plan["code"] for plan in PLAN_CATALOG if plan["code"] not in overrides]
            if missing:
                raise CLIError(
                    f"--non-interactive requires plan overrides (missing: {', '.join(missing)})."
                )
        return overrides

    def _prompt_plan_amount(self, plan_name: str, default_cents: int) -> int:
        if self.non_interactive:
            return default_cents

        default_display = f"{Decimal(default_cents) / Decimal(100):.2f}"
        while True:
            prompt = (
                f"Monthly price for {plan_name} in {self.currency.upper()} "
                f"(default {default_display}): "
            )
            raw = input(prompt).strip()
            if not raw:
                return default_cents
            try:
                cents = self._parse_amount_cents(raw)
            except CLIError as exc:
                console.warn(str(exc), topic="stripe")
                continue
            return cents

    def _parse_amount_cents(self, raw: str) -> int:
        try:
            amount = Decimal(raw)
        except InvalidOperation as exc:
            raise CLIError("Enter a numeric amount (e.g., 29 or 29.99).") from exc
        if amount <= 0:
            raise CLIError("Amount must be greater than zero.")
        return int((amount * 100).to_integral_value())

    def _provision_plans(self, api_key: str, plan_amounts: dict[str, int]) -> dict[str, str]:
        assert stripe is not None  # for type checkers
        stripe.api_key = api_key
        price_map: dict[str, str] = {}
        for plan in PLAN_CATALOG:
            code = plan["code"]
            amount = plan_amounts[code]
            product: Any = self._ensure_product(code=code, name=plan["name"])
            price: Any = self._ensure_price(product.id, code, amount)
            price_map[code] = price.id
            console.success(
                f"Configured {plan['name']} "
                f"({self.currency.upper()} {amount / 100:.2f}) → {price.id}",
                topic="stripe",
            )
        return price_map

    def _ensure_product(self, *, code: str, name: str) -> Any:
        assert stripe is not None
        search_query = f"metadata['{PLAN_METADATA_KEY}']:'{code}'"
        products = stripe.Product.search(query=search_query, limit=1)
        if products.data:
            product: Any = products.data[0]
            if product.name != name:
                stripe.Product.modify(product.id, name=name)
            return product
        return stripe.Product.create(name=name, metadata={PLAN_METADATA_KEY: code})

    def _ensure_price(self, product_id: str, plan_code: str, amount_cents: int) -> Any:
        assert stripe is not None
        prices: Any = stripe.Price.list(product=product_id, active=True, limit=100)
        for price in prices.auto_paging_iter():
            recurring = getattr(price, "recurring", None) or {}
            if (
                price.currency == self.currency
                and price.unit_amount == amount_cents
                and recurring.get("interval") == "month"
                and recurring.get("trial_period_days") == self.trial_days
            ):
                return price
        return stripe.Price.create(
            product=product_id,
            currency=self.currency,
            unit_amount=amount_cents,
            nickname=f"{plan_code.title()} Monthly",
            recurring={"interval": "month", "trial_period_days": self.trial_days},
            metadata={PLAN_METADATA_KEY: plan_code},
        )

    def _update_env(
        self,
        env_local: EnvFile,
        price_map: dict[str, str],
        secret: str,
        webhook: str,
    ) -> None:
        env_local.set("STRIPE_SECRET_KEY", secret)
        env_local.set("STRIPE_WEBHOOK_SECRET", webhook)
        env_local.set("STRIPE_PRODUCT_PRICE_MAP", json.dumps(price_map, separators=(",", ":")))
        env_local.set("ENABLE_BILLING", "true")
        env_local.save()

    @staticmethod
    def _graceful_exit(signum: int, _frame: FrameType | None) -> None:
        console.warn(f"Received signal {signum}. Exiting.")
        raise SystemExit(1)

    @staticmethod
    def _prompt_yes_no(question: str, *, default: bool = True) -> bool:
        hint = "Y/n" if default else "y/N"
        while True:
            answer = input(f"{question} ({hint}) ").strip().lower()
            if not answer:
                return default
            if answer in {"y", "yes"}:
                return True
            if answer in {"n", "no"}:
                return False
            console.warn("Please answer yes or no.")

    @staticmethod
    def _prompt_input(question: str) -> str:
        return input(f"{question}: ").strip()

    @staticmethod
    def _run_command(
        cmd: list[str], *, check: bool = True, capture_output: bool = False
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            cmd,
            check=check,
            text=True,
            capture_output=capture_output,
        )

    @staticmethod
    def _run_interactive(cmd: list[str]) -> None:
        console.info(" ".join(cmd), topic="exec")
        subprocess.run(cmd, check=True)

    @staticmethod
    def _open_url(url: str) -> None:
        import sys

        if sys.platform.startswith("darwin"):
            opener = "open"
        elif os.name == "nt":
            opener = "start"
        else:
            opener = "xdg-open"
        try:
            subprocess.Popen([opener, url])
            console.info(f"Opened {url} in your browser.")
        except OSError:
            console.warn(f"Unable to open {url}. Please visit it manually.")

    @staticmethod
    def _mask(value: str | None) -> str:
        if not value:
            return "(empty)"
        if len(value) <= 8:
            return "*" * len(value)
        return f"{value[:4]}…{value[-4:]}"
