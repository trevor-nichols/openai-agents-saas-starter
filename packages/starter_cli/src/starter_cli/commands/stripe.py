from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import signal
import subprocess
import time
import uuid
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
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
DEFAULT_WEBHOOK_FORWARD_URL = "http://localhost:8000/api/v1/webhooks/stripe"
WHSEC_PATTERN = re.compile(r"whsec_[A-Za-z0-9]+")


class PlanConfig(TypedDict):
    code: str
    name: str
    default_cents: int


PLAN_CATALOG: tuple[PlanConfig, ...] = (
    {"code": "starter", "name": "Starter", "default_cents": 2000},
    {"code": "pro", "name": "Pro", "default_cents": 9900},
)
PLAN_METADATA_KEY = "starter_cli_plan_code"


class StripeCLIBase:
    """Shared Stripe CLI helpers used across flows."""

    skip_stripe_cli: bool
    non_interactive: bool

    def _ensure_stripe_cli(self) -> None:
        if self.skip_stripe_cli:
            return
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

    def _capture_webhook_secret(self, forward_url: str, *, timeout_sec: float = 15.0) -> str:
        if not self.skip_stripe_cli:
            self._ensure_stripe_cli()
        console.info(
            f"Requesting webhook secret via Stripe CLI (forward → {forward_url})",
            topic="stripe",
        )
        listener_cmd = [
            "stripe",
            "listen",
            "--print-secret",
            "--forward-to",
            forward_url,
        ]
        try:
            process = subprocess.Popen(
                listener_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
        except FileNotFoundError as exc:  # pragma: no cover - runtime dependency
            raise CLIError(
                "Stripe CLI not found. Install from https://docs.stripe.com/stripe-cli."
            ) from exc

        secret: str | None = None
        last_line: str | None = None
        start = time.monotonic()
        try:
            if process.stdout is None:  # pragma: no cover - defensive
                raise CLIError("Unable to read output from Stripe CLI.")
            for line in process.stdout:
                last_line = line.rstrip()
                match = WHSEC_PATTERN.search(last_line)
                if match:
                    secret = match.group(0)
                    break
                if (time.monotonic() - start) > timeout_sec:
                    break
        finally:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:  # pragma: no cover - defensive
                process.kill()

        if not secret:
            detail = f" Last Stripe CLI output: {last_line}" if last_line else ""
            raise CLIError(
                "Stripe CLI did not emit a webhook signing secret. "
                "Ensure `stripe login` has completed and try again." + detail
            )

        console.success("Captured webhook signing secret via Stripe CLI.", topic="stripe")
        return secret

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
    def _mask(value: str | None) -> str:
        if not value:
            return "(empty)"
        if len(value) <= 8:
            return "*" * len(value)
        return f"{value[:4]}…{value[-4:]}"

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
        "--auto-webhook-secret",
        action="store_true",
        help="Use Stripe CLI to generate a webhook signing secret (interactive only).",
    )
    setup_parser.add_argument(
        "--webhook-forward-url",
        default=DEFAULT_WEBHOOK_FORWARD_URL,
        help=(
            "Forwarding URL passed to `stripe listen --forward-to` "
            "when generating webhook secrets."
        ),
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

    webhook_parser = stripe_subparsers.add_parser(
        "webhook-secret",
        help="Capture a Stripe webhook signing secret via Stripe CLI.",
    )
    webhook_parser.add_argument(
        "--forward-url",
        default=DEFAULT_WEBHOOK_FORWARD_URL,
        help="Forwarding URL passed to Stripe CLI (default: local FastAPI webhook endpoint).",
    )
    webhook_parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print the secret without writing .env.local.",
    )
    webhook_parser.add_argument(
        "--skip-stripe-cli",
        action="store_true",
        help="Skip Stripe CLI verification (assumes the CLI is installed and authenticated).",
    )
    webhook_parser.set_defaults(handler=handle_webhook_secret)

    dispatch_parser = stripe_subparsers.add_parser(
        "dispatches",
        help="Inspect and replay stored Stripe webhook dispatches.",
    )
    dispatch_subparsers = dispatch_parser.add_subparsers(dest="dispatch_command")

    dispatch_list = dispatch_subparsers.add_parser(
        "list",
        help="List stored Stripe dispatches.",
    )
    dispatch_list.add_argument(
        "--status",
        choices=[*_dispatch_status_choices(), "all"],
        default="failed",
        help="Filter by status (default: failed). Use 'all' to show every status.",
    )
    dispatch_list.add_argument(
        "--handler",
        default="billing_sync",
        help="Handler name to filter (default: billing_sync).",
    )
    dispatch_list.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum rows to return (default: 20).",
    )
    dispatch_list.add_argument(
        "--page",
        type=int,
        default=1,
        help="Page number (1-indexed).",
    )
    dispatch_list.set_defaults(handler=handle_dispatch_list)

    dispatch_replay = dispatch_subparsers.add_parser(
        "replay",
        help="Replay stored dispatches through the dispatcher.",
    )
    dispatch_replay.add_argument(
        "--dispatch-id",
        action="append",
        help="Dispatch UUID(s) to replay.",
    )
    dispatch_replay.add_argument(
        "--event-id",
        action="append",
        help="Replay dispatches derived from Stripe event IDs.",
    )
    dispatch_replay.add_argument(
        "--status",
        choices=_dispatch_status_choices(),
        help="Replay all dispatches with the given status (respects --limit).",
    )
    dispatch_replay.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Limit when replaying by status (default: 5).",
    )
    dispatch_replay.add_argument(
        "--handler",
        default="billing_sync",
        help="Handler name to target (default: billing_sync).",
    )
    dispatch_replay.add_argument(
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt.",
    )
    dispatch_replay.set_defaults(handler=handle_dispatch_replay)

    fixtures_parser = dispatch_subparsers.add_parser(
        "validate-fixtures",
        help="Validate local Stripe fixture JSON files.",
    )
    fixtures_parser.add_argument(
        "--path",
        default="apps/api-service/tests/fixtures/stripe",
        help=(
            "Directory containing *.json fixtures "
            "(default: apps/api-service/tests/fixtures/stripe)."
        ),
    )
    fixtures_parser.set_defaults(handler=handle_dispatch_validate_fixtures)


def handle_stripe_setup(args: argparse.Namespace, ctx: CLIContext) -> int:
    flow = StripeSetupFlow(
        ctx=ctx,
        currency=args.currency,
        trial_days=args.trial_days,
        non_interactive=args.non_interactive,
        secret_key=args.secret_key,
        webhook_secret=args.webhook_secret,
        auto_webhook_secret=args.auto_webhook_secret,
        webhook_forward_url=args.webhook_forward_url,
        plan_overrides=args.plan or [],
        skip_postgres=args.skip_postgres_check,
        skip_stripe_cli=args.skip_stripe_cli,
    )
    flow.run()
    return 0


def handle_webhook_secret(args: argparse.Namespace, ctx: CLIContext) -> int:
    flow = WebhookSecretFlow(
        ctx=ctx,
        forward_url=args.forward_url,
        print_only=args.print_only,
        skip_stripe_cli=args.skip_stripe_cli,
    )
    flow.run()
    return 0


@dataclass(slots=True)
class StripeSetupFlow(StripeCLIBase):
    ctx: CLIContext
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
        webhook_secret = self._collect_webhook_secret(aggregated.get("STRIPE_WEBHOOK_SECRET"))

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
                "Missing dependency 'stripe'. "
                "Install with `pip install './apps/api-service[dev]'`."
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
        if self._prompt_yes_no("Start or refresh the local Postgres stack via `just dev-up`?"):
            try:
                self._run_interactive(["just", "dev-up"])
            except (FileNotFoundError, subprocess.CalledProcessError) as exc:
                console.warn(
                    f"`just dev-up` failed ({exc}). Fix Postgres manually.",
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

    def _collect_webhook_secret(self, existing: str | None) -> str:
        if self.webhook_secret:
            return self.webhook_secret

        if self.non_interactive:
            return self._obtain_secret(
                "Stripe webhook secret",
                existing,
                provided=self.webhook_secret,
            )

        if existing and self._prompt_yes_no(
            f"Reuse existing webhook secret {self._mask(existing)}?", default=True
        ):
            return existing

        if self.auto_webhook_secret or self._prompt_yes_no(
            "Generate a webhook signing secret via Stripe CLI now?",
            default=True,
        ):
            return self._capture_webhook_secret(self.webhook_forward_url)

        return self._obtain_secret("Stripe webhook secret", existing, provided=None)

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

        self._update_frontend_env()

    def _update_frontend_env(self) -> None:
        frontend_path = self.ctx.project_root / "apps" / "web-app" / ".env.local"
        if not frontend_path.parent.exists():
            console.warn(
                "Frontend directory missing; skipped web-app/.env.local.",
                topic="stripe",
            )
            return

        env_frontend = EnvFile(frontend_path)
        env_frontend.set("NEXT_PUBLIC_ENABLE_BILLING", "true")
        env_frontend.save()
        console.success("Updated web-app/.env.local", topic="stripe")

    @staticmethod
    def _graceful_exit(signum: int, _frame: FrameType | None) -> None:
        console.warn(f"Received signal {signum}. Exiting.")
        raise SystemExit(1)

@dataclass(slots=True)
class WebhookSecretFlow(StripeCLIBase):
    ctx: CLIContext
    forward_url: str
    print_only: bool
    skip_stripe_cli: bool
    non_interactive: bool = False

    def run(self) -> None:
        if not self.skip_stripe_cli:
            self._ensure_stripe_cli()
        secret = self._capture_webhook_secret(self.forward_url)

        if self.print_only:
            console.info("Webhook signing secret (not saved):", topic="stripe")
            print(secret)
            return

        env_local = EnvFile(self.ctx.project_root / ".env.local")
        env_local.set("STRIPE_WEBHOOK_SECRET", secret)
        env_local.save()
        os.environ["STRIPE_WEBHOOK_SECRET"] = secret
        console.success(
            f"Saved STRIPE_WEBHOOK_SECRET={self._mask(secret)} to .env.local",
            topic="stripe",
        )


# --- Dispatch inspection/replay helpers ---


def handle_dispatch_list(args: argparse.Namespace, _ctx: CLIContext) -> int:
    return _run_dispatch_task(
        lambda: _list_dispatches(
            handler=args.handler,
            status=args.status,
            limit=args.limit,
            page=args.page,
        )
    )


def handle_dispatch_replay(args: argparse.Namespace, _ctx: CLIContext) -> int:
    return _run_dispatch_task(
        lambda: _replay_dispatches(
            dispatch_ids=args.dispatch_id,
            event_ids=args.event_id,
            status=args.status,
            limit=args.limit,
            handler=args.handler,
            assume_yes=args.yes,
        )
    )


def handle_dispatch_validate_fixtures(args: argparse.Namespace, ctx: CLIContext) -> int:
    directory = Path(args.path)
    if not directory.is_absolute():
        directory = (ctx.project_root / directory).resolve()
    if not directory.exists():
        raise CLIError(f"Fixture directory '{directory}' not found.")
    failures = 0
    for file in sorted(directory.glob("*.json")):
        try:
            json.loads(file.read_text(encoding="utf-8"))
            console.success(f"{file.relative_to(directory)}", topic="stripe-fixtures")
        except json.JSONDecodeError as exc:
            failures += 1
            console.error(f"{file}: invalid JSON ({exc})", topic="stripe-fixtures")
    if failures:
        raise CLIError(f"Fixture validation failed ({failures} files).")
    return 0


def _dispatch_status_choices() -> tuple[str, ...]:
    """Return dispatch status values without hard-importing the backend package at startup.

    The CLI is packaged independently from the FastAPI app (see MILESTONE_PACKAGES);
    importing `app.*` during parser construction breaks commands like `util run-with-env`
    that don't need the backend. We attempt the import lazily and fall back to the
    known status literals if the backend isn't on `sys.path`.
    """
    from importlib import import_module

    try:
        models = import_module("app.infrastructure.persistence.stripe.models")
    except ModuleNotFoundError:
        return ("pending", "in_progress", "failed", "completed")

    StripeDispatchStatus = models.StripeDispatchStatus
    return tuple(status.value for status in StripeDispatchStatus)


def _run_dispatch_task(task: Callable[[], Awaitable[int]]) -> int:
    async def _runner() -> int:
        from importlib import import_module

        config_module = import_module("app.core.config")
        db_module = import_module("app.infrastructure.db")
        dispose_engine = db_module.dispose_engine

        try:
            result = await task()
        finally:
            await dispose_engine()
            config_module.get_settings.cache_clear()
        return result

    try:
        return asyncio.run(_runner())
    except CLIError:
        raise
    except Exception as exc:  # pragma: no cover - runtime safety
        raise CLIError(str(exc)) from exc


async def _init_dispatch_repo():
    from importlib import import_module

    config_module = import_module("app.core.config")
    db_module = import_module("app.infrastructure.db")
    billing_repo_module = import_module("app.infrastructure.persistence.billing")
    stripe_repo_module = import_module("app.infrastructure.persistence.stripe.repository")
    billing_service_module = import_module("app.services.billing.billing_service")

    init_engine = db_module.init_engine
    get_async_sessionmaker = db_module.get_async_sessionmaker
    PostgresBillingRepository = billing_repo_module.PostgresBillingRepository
    StripeEventRepository = stripe_repo_module.StripeEventRepository
    billing_service = billing_service_module.billing_service

    config_module.get_settings.cache_clear()
    await init_engine(run_migrations=False)
    session_factory = get_async_sessionmaker()
    billing_service.set_repository(PostgresBillingRepository(session_factory))
    return StripeEventRepository(session_factory)


async def _list_dispatches(
    *,
    handler: str,
    status: str,
    limit: int,
    page: int,
) -> int:
    repo = await _init_dispatch_repo()
    status_filter = None if status == "all" else status
    offset = max(page - 1, 0) * limit
    dispatches = await repo.list_dispatches(
        handler=handler,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    if not dispatches:
        console.info("No dispatches found.", topic="stripe")
        return 0

    console.info(f"Page {page} (limit {limit})", topic="stripe")
    for dispatch, event in dispatches:
        print(
            f"{dispatch.id}\t{dispatch.status}\thandler={dispatch.handler}\t"
            f"attempts={dispatch.attempts}\tevent={event.stripe_event_id} "
            f"({event.event_type})\ttenant={event.tenant_hint}"
        )
    return 0


async def _replay_dispatches(
    *,
    dispatch_ids: list[str] | None,
    event_ids: list[str] | None,
    status: str | None,
    limit: int,
    handler: str,
    assume_yes: bool,
) -> int:
    repo = await _init_dispatch_repo()
    return await replay_dispatches_with_repo(
        repo,
        dispatch_ids=dispatch_ids,
        event_ids=event_ids,
        status=status,
        limit=limit,
        handler=handler,
        assume_yes=assume_yes,
    )


async def replay_dispatches_with_repo(
    repo: Any,
    *,
    dispatch_ids: list[str] | None,
    event_ids: list[str] | None,
    status: str | None,
    limit: int,
    handler: str,
    assume_yes: bool,
    dispatcher: Any | None = None,
    billing: Any | None = None,
    confirm: Callable[[list[uuid.UUID]], bool] | None = None,
) -> int:
    from importlib import import_module

    billing_service_module = import_module("app.services.billing.billing_service")
    dispatcher_module = import_module("app.services.billing.stripe.dispatcher")

    billing_service = billing_service_module.billing_service
    stripe_event_dispatcher = dispatcher_module.stripe_event_dispatcher

    dispatcher = dispatcher or stripe_event_dispatcher
    billing = billing or billing_service

    if dispatcher is None or billing is None:
        raise CLIError("Stripe dispatcher or billing service unavailable.")

    dispatcher.configure(repository=repo, billing=billing)

    targets: list[uuid.UUID] = []
    if dispatch_ids:
        targets.extend(uuid.UUID(value) for value in dispatch_ids)
    elif event_ids:
        for event_id in event_ids:
            event = await repo.get_by_event_id(event_id)
            if event is None:
                console.warn(f"Event {event_id} not found; skipping.", topic="stripe")
                continue
            dispatch = await repo.ensure_dispatch(event_id=event.id, handler=handler)
            targets.append(dispatch.id)
    elif status:
        rows = await repo.list_dispatches(handler=handler, status=status, limit=limit)
        targets.extend(row[0].id for row in rows)
    else:
        raise CLIError("Provide --dispatch-id, --event-id, or --status for replay.")

    if not targets:
        console.info("No dispatches to replay.", topic="stripe")
        return 0

    confirmation = confirm or _confirm_replay
    if not assume_yes and not confirmation(targets):
        console.info("Replay aborted by user.", topic="stripe")
        return 0

    for dispatch_id in targets:
        try:
            result = await dispatcher.replay_dispatch(dispatch_id)
            when = result.processed_at.isoformat() if result.processed_at else "n/a"
            console.success(
                f"Replayed dispatch {dispatch_id} (processed_at={when})",
                topic="stripe",
            )
        except Exception as exc:  # pragma: no cover - runtime
            console.error(f"Failed to replay {dispatch_id}: {exc}", topic="stripe")
    return 0


def _confirm_replay(targets: list[uuid.UUID]) -> bool:
    preview = "\n".join(str(t) for t in targets[:5])
    if len(targets) > 5:
        preview += f"\n...and {len(targets) - 5} more"
    console.info("About to replay the following dispatch IDs:", topic="stripe")
    print(preview)
    answer = input("Proceed? [y/N]: ").strip().lower()
    return answer in {"y", "yes"}
