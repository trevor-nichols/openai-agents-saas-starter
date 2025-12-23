from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine

from starter_cli.adapters.env import (
    EnvFile,
    aggregate_env_values,
    build_env_scope,
    expand_env_placeholders,
)
from starter_cli.core import CLIContext, CLIError

from .stripe import DEFAULT_WEBHOOK_FORWARD_URL, PLAN_CATALOG, StripeSetupFlow

_ENV_KEYS = (
    "DATABASE_URL",
    "ENABLE_BILLING",
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "STRIPE_PRODUCT_PRICE_MAP",
)
_PLAN_CODES = tuple(plan["code"] for plan in PLAN_CATALOG)


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    release_parser = subparsers.add_parser("release", help="Release automation workflows.")
    release_subparsers = release_parser.add_subparsers(dest="release_command")

    db_parser = release_subparsers.add_parser(
        "db",
        help="Run migrations, Stripe seeding, and billing plan verification.",
    )
    db_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help=(
            "Fail instead of prompting for inputs "
            "(requires explicit Stripe params or --skip-stripe)."
        ),
    )
    db_parser.add_argument(
        "--skip-stripe",
        action="store_true",
        help="Skip the embedded Stripe setup flow (attach manual evidence separately).",
    )
    db_parser.add_argument(
        "--skip-db-checks",
        action="store_true",
        help="Skip billing plan verification queries.",
    )
    db_parser.add_argument(
        "--summary-path",
        help=(
            "Optional path for the JSON summary artifact "
            "(defaults to var/reports/db-release-<timestamp>.json)."
        ),
    )
    db_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the JSON summary to stdout after writing the artifact.",
    )
    db_parser.add_argument(
        "--plan",
        action="append",
        metavar="CODE=CENTS",
        help=(
            "Override Stripe plan amount when --non-interactive is used "
            "(forwarded to stripe setup)."
        ),
    )
    db_parser.set_defaults(handler=handle_db_release)


def handle_db_release(args: argparse.Namespace, ctx: CLIContext) -> int:
    workflow = DatabaseReleaseWorkflow(ctx=ctx, args=args)
    return workflow.run()


@dataclass(slots=True)
class StepResult:
    name: str
    status: str
    detail: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class DatabaseReleaseWorkflow:
    def __init__(self, *, ctx: CLIContext, args: argparse.Namespace) -> None:
        self.ctx = ctx
        self.console = ctx.console
        self.args = args
        self.project_root = ctx.project_root
        self.timestamp = datetime.now(UTC)
        self.summary_path = self._resolve_summary_path(args.summary_path)
        self.env_files = self._load_env_files()
        self.aggregated_env = aggregate_env_values(self.env_files, _ENV_KEYS)
        self.env_scope = build_env_scope(self.env_files)
        self.database_url = self._expand_env(self.aggregated_env.get("DATABASE_URL"))
        self.enable_billing = self._as_bool(self.aggregated_env.get("ENABLE_BILLING"))
        self.step_results: list[StepResult] = []
        self.plan_snapshot: list[dict[str, Any]] = []
        self.alembic_revision: str | None = None
        self.git_sha = self._git_sha()
        self.settings = ctx.optional_settings()
        self.summary_status = "success"

    def run(self) -> int:
        try:
            self._run_migrations()
            self._capture_alembic_revision()
            self._maybe_run_stripe_setup()
            self._maybe_verify_billing_plans()
        except CLIError as exc:
            self.summary_status = "failed"
            self.console.error(str(exc), topic="release")
        except Exception as exc:  # pragma: no cover - defensive catch
            self.summary_status = "failed"
            self.console.error(f"Unexpected release failure: {exc}", topic="release")
        finally:
            self._write_summary()

        summary_display = self._relative_summary_path()
        if self.summary_status != "success":
            self.console.error(
                f"Release workflow failed; summary saved to {summary_display}",
                topic="release",
            )
            if self.args.json:
                print(self.summary_path.read_text(encoding="utf-8"))
            return 1
        self.console.success(
            f"Release workflow succeeded; summary saved to {summary_display}",
            topic="release",
        )
        if self.args.json:
            print(self.summary_path.read_text(encoding="utf-8"))
        return 0

    # ------------------------------------------------------------------ #
    # Steps
    # ------------------------------------------------------------------ #
    def _run_migrations(self) -> None:
        self._execute_step(
            name="migrations",
            func=lambda: self._run_command(["just", "migrate"], "Ran `just migrate`."),
        )

    def _capture_alembic_revision(self) -> None:
        def _capture() -> str:
            cmd = [
                "hatch",
                "run",
                "alembic",
                "-c",
                "apps/api-service/alembic.ini",
                "current",
            ]
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                check=True,
                capture_output=True,
                text=True,
            )
            output = (result.stdout or result.stderr or "").strip()
            self.alembic_revision = output or None
            return output or "Captured current Alembic revision."

        self._execute_step(name="alembic_revision", func=_capture)

    def _maybe_run_stripe_setup(self) -> None:
        if self.args.skip_stripe:
            self._record_step(
                "stripe_setup",
                "skipped",
                "Skipped Stripe provisioning (requested via --skip-stripe).",
            )
            return

        if not self.enable_billing:
            self._record_step(
                "stripe_setup",
                "skipped",
                "ENABLE_BILLING is false; skipping Stripe setup.",
            )
            return

        def _run() -> str:
            flow = StripeSetupFlow(
                ctx=self.ctx,
                currency="usd",
                trial_days=14,
                non_interactive=self.args.non_interactive,
                secret_key=self.aggregated_env.get("STRIPE_SECRET_KEY"),
                webhook_secret=self.aggregated_env.get("STRIPE_WEBHOOK_SECRET"),
                auto_webhook_secret=False,
                webhook_forward_url=DEFAULT_WEBHOOK_FORWARD_URL,
                plan_overrides=self.args.plan or [],
                skip_postgres=True,
                skip_stripe_cli=self.args.non_interactive,
            )
            flow.run()
            return "Stripe provisioning completed."

        self._execute_step(name="stripe_setup", func=_run)

    def _maybe_verify_billing_plans(self) -> None:
        if self.args.skip_db_checks:
            self._record_step(
                "billing_plan_verification",
                "skipped",
                "Skipped plan verification (requested via --skip-db-checks).",
            )
            return

        database_url = self.database_url
        if not database_url:
            raise CLIError("DATABASE_URL is not configured; cannot verify billing plans.")

        async def _verify() -> list[dict[str, Any]]:
            engine = create_async_engine(database_url)
            try:
                async with engine.connect() as conn:
                    result = await conn.execute(
                        text(
                            "SELECT code, stripe_price_id, is_active "
                            "FROM billing_plans ORDER BY code"
                        )
                    )
                    rows = result.fetchall()
            except SQLAlchemyError as exc:  # pragma: no cover - driver errors
                raise CLIError(f"Billing plan query failed: {exc}") from exc
            finally:
                await engine.dispose()

            plan_map = {str(row._mapping.get("code")): row._mapping for row in rows}
            snapshot: list[dict[str, Any]] = []
            for code in _PLAN_CODES:
                row = plan_map.get(code)
                if not row:
                    snapshot.append(
                        {
                            "code": code,
                            "status": "missing",
                            "stripe_price_id": None,
                            "is_active": False,
                        }
                    )
                    continue
                stripe_price_id = row.get("stripe_price_id")
                is_active = bool(row.get("is_active"))
                if not stripe_price_id:
                    status = "missing_price_id"
                elif not is_active:
                    status = "inactive"
                else:
                    status = "ok"
                snapshot.append(
                    {
                        "code": code,
                        "status": status,
                        "stripe_price_id": stripe_price_id,
                        "is_active": is_active,
                    }
                )
            return snapshot

        def _sync_verify() -> str:
            self.plan_snapshot = asyncio.run(_verify())
            missing = [plan for plan in self.plan_snapshot if plan["status"] != "ok"]
            if missing:
                codes = ", ".join(plan["code"] for plan in missing)
                raise CLIError(f"Billing plan verification failed for: {codes}")
            return "Billing plan verification succeeded."

        self._execute_step(name="billing_plan_verification", func=_sync_verify)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _execute_step(self, name: str, func: Callable[[], str]) -> None:
        try:
            detail = func()
        except CLIError as exc:
            self._record_step(name, "failed", str(exc))
            raise
        except subprocess.CalledProcessError as exc:
            self._record_step(name, "failed", exc.stderr or str(exc))
            raise CLIError(f"Command failed for step '{name}': {exc}") from exc
        else:
            self._record_step(name, "success", detail)

    def _record_step(self, name: str, status: str, detail: str | None) -> None:
        self.step_results.append(StepResult(name=name, status=status, detail=detail))

    def _write_summary(self) -> None:
        payload = {
            "status": self.summary_status,
            "executed_at": self.timestamp.isoformat(),
            "environment": getattr(self.settings, "environment", None),
            "git_sha": self.git_sha,
            "alembic_revision": self.alembic_revision,
            "steps": [asdict(step) for step in self.step_results],
            "billing_plans": self.plan_snapshot,
            "options": {
                "non_interactive": self.args.non_interactive,
                "skip_stripe": self.args.skip_stripe,
                "skip_db_checks": self.args.skip_db_checks,
            },
            "stripe_price_map": self._parse_price_map(),
            "secrets": {
                "stripe_secret_key": self._mask(self.aggregated_env.get("STRIPE_SECRET_KEY")),
                "stripe_webhook_secret": self._mask(
                    self.aggregated_env.get("STRIPE_WEBHOOK_SECRET")
                ),
            },
        }
        self.summary_path.parent.mkdir(parents=True, exist_ok=True)
        self.summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _resolve_summary_path(self, override: str | None) -> Path:
        if override:
            path = Path(override)
            return path if path.is_absolute() else self.project_root / path
        slug = self.timestamp.strftime("%Y%m%dT%H%M%SZ")
        return self.project_root / "var" / "reports" / f"db-release-{slug}.json"

    def _relative_summary_path(self) -> str:
        try:
            return str(self.summary_path.relative_to(self.project_root))
        except ValueError:  # pragma: no cover - custom paths outside repo
            return str(self.summary_path)

    def _load_env_files(self) -> tuple[EnvFile, EnvFile, EnvFile]:
        env_local = EnvFile(self.project_root / "apps" / "api-service" / ".env.local")
        env_fallback = EnvFile(self.project_root / "apps" / "api-service" / ".env")
        env_compose = EnvFile(self.project_root / ".env.compose")
        return (env_local, env_fallback, env_compose)

    def _expand_env(self, value: str | None) -> str | None:
        if not value:
            return None
        return expand_env_placeholders(value, self.env_scope)

    @staticmethod
    def _as_bool(value: str | None) -> bool:
        if value is None:
            return False
        return value.strip().lower() in {"1", "true", "yes", "on"}

    def _parse_price_map(self) -> dict[str, Any] | None:
        raw = self.aggregated_env.get("STRIPE_PRODUCT_PRICE_MAP")
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"raw": raw}

    @staticmethod
    def _mask(value: str | None) -> str | None:
        if not value:
            return None
        if len(value) <= 4:
            return "*" * len(value)
        return f"{value[:4]}…{value[-4:]}"

    def _git_sha(self) -> str | None:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):  # pragma: no cover
            return None
        return result.stdout.strip() or None

    def _run_command(self, cmd: Sequence[str], success_detail: str) -> str:
        subprocess.run(cmd, cwd=self.project_root, check=True)
        return success_detail


__all__ = ["register", "handle_db_release"]
