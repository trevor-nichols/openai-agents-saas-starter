from __future__ import annotations

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

from starter_console.adapters.env import (
    EnvFile,
    aggregate_env_values,
    build_env_scope,
    expand_env_placeholders,
)
from starter_console.core import CLIContext, CLIError
from starter_console.services.stripe.catalog import PLAN_CATALOG
from starter_console.workflows.stripe import (
    DEFAULT_WEBHOOK_FORWARD_URL,
    StripeSetupConfig,
    run_stripe_setup,
)

_ENV_KEYS = (
    "DATABASE_URL",
    "ENABLE_BILLING",
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "STRIPE_PRODUCT_PRICE_MAP",
)
_PLAN_CODES = tuple(plan.code for plan in PLAN_CATALOG)


@dataclass(slots=True)
class StepResult:
    name: str
    status: str
    detail: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DatabaseReleaseConfig:
    non_interactive: bool = False
    skip_stripe: bool = False
    skip_db_checks: bool = False
    summary_path: str | None = None
    plan_overrides: Sequence[str] | None = None
    json_output: bool = False


class DatabaseReleaseWorkflow:
    def __init__(self, *, ctx: CLIContext, config: DatabaseReleaseConfig) -> None:
        self.ctx = ctx
        self.console = ctx.console
        self.config = config
        self.project_root = ctx.project_root
        self.timestamp = datetime.now(UTC)
        self.summary_path = self._resolve_summary_path(config.summary_path)
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
            if self.config.json_output:
                print(self.summary_path.read_text(encoding="utf-8"))
            return 1
        self.console.success(
            f"Release workflow succeeded; summary saved to {summary_display}",
            topic="release",
        )
        if self.config.json_output:
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
        if self.config.skip_stripe:
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
            config = StripeSetupConfig(
                currency="usd",
                trial_days=14,
                non_interactive=self.config.non_interactive,
                secret_key=self.aggregated_env.get("STRIPE_SECRET_KEY"),
                webhook_secret=self.aggregated_env.get("STRIPE_WEBHOOK_SECRET"),
                auto_webhook_secret=False,
                webhook_forward_url=DEFAULT_WEBHOOK_FORWARD_URL,
                plan_overrides=list(self.config.plan_overrides or ()),
                skip_postgres=True,
                skip_stripe_cli=self.config.non_interactive,
            )
            run_stripe_setup(self.ctx, config)
            return "Stripe provisioning completed."

        self._execute_step("stripe_setup", _run)

    def _maybe_verify_billing_plans(self) -> None:
        if self.config.skip_db_checks:
            self._record_step(
                "billing_plan_check",
                "skipped",
                "Skipped billing plan verification (requested via --skip-db-checks).",
            )
            return

        if not self.enable_billing:
            self._record_step(
                "billing_plan_check",
                "skipped",
                "ENABLE_BILLING is false; skipping billing plan checks.",
            )
            return

        database_url = self.database_url
        if database_url is None:
            raise CLIError("DATABASE_URL is required for billing plan verification.")

        async def _verify() -> str:
            engine = create_async_engine(database_url, pool_pre_ping=True)
            try:
                async with engine.begin() as conn:
                    result = await conn.execute(
                        text(
                            "SELECT code, stripe_price_id, is_active "
                            "FROM billing_plans ORDER BY code"
                        )
                    )
                    rows = [dict(row) for row in result.mappings().all()]
                    self.plan_snapshot = rows
            except SQLAlchemyError as exc:
                raise CLIError(f"Billing plan verification failed: {exc}") from exc
            finally:
                await engine.dispose()

            missing = {code for code in _PLAN_CODES if code not in {r["code"] for r in rows}}
            if missing:
                return f"Billing plans missing: {', '.join(sorted(missing))}."
            return "Billing plan verification complete."

        self._execute_step("billing_plan_check", lambda: asyncio.run(_verify()))

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _execute_step(self, name: str, func: Callable[[], str]) -> None:
        try:
            detail = func()
            self._record_step(name, "success", detail)
        except CLIError as exc:
            self._record_step(name, "failed", str(exc))
            raise

    def _record_step(self, name: str, status: str, detail: str | None) -> None:
        self.step_results.append(StepResult(name=name, status=status, detail=detail))

    def _run_command(self, command: Sequence[str], success_detail: str) -> str:
        try:
            subprocess.run(
                list(command),
                cwd=self.project_root,
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise CLIError(f"Command not found: {exc}") from exc
        except subprocess.CalledProcessError as exc:
            raise CLIError(
                f"Command failed ({' '.join(command)}): {(exc.stderr or exc.stdout).strip()}"
            ) from exc
        return success_detail

    def _write_summary(self) -> None:
        payload = {
            "version": "v1",
            "timestamp": self.timestamp.isoformat(),
            "status": self.summary_status,
            "git_sha": self.git_sha,
            "summary_path": str(self.summary_path),
            "alembic_revision": self.alembic_revision,
            "steps": [asdict(step) for step in self.step_results],
            "billing_plans": self.plan_snapshot,
        }
        self.summary_path.parent.mkdir(parents=True, exist_ok=True)
        self.summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _resolve_summary_path(self, override: str | None) -> Path:
        if override:
            return Path(override).expanduser().resolve()
        timestamp = self.timestamp.strftime("%Y%m%d-%H%M%S")
        return self.project_root / "var" / "reports" / f"db-release-{timestamp}.json"

    def _relative_summary_path(self) -> str:
        try:
            return str(self.summary_path.relative_to(self.project_root))
        except ValueError:
            return str(self.summary_path)

    def _load_env_files(self) -> list[EnvFile]:
        files = list(self.ctx.env_files)
        return [EnvFile(path) for path in files]

    def _expand_env(self, value: str | None) -> str | None:
        if not value:
            return None
        return expand_env_placeholders(value, self.env_scope)

    @staticmethod
    def _as_bool(value: str | None) -> bool:
        if not value:
            return False
        return value.lower() in {"1", "true", "yes", "on"}

    def _git_sha(self) -> str | None:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_root,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()
        except Exception:
            return None


__all__ = ["DatabaseReleaseConfig", "DatabaseReleaseWorkflow", "StepResult"]
