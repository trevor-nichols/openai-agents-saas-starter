from __future__ import annotations

import os
import secrets
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from starter_shared.config import get_settings

from starter_cli.cli.common import CLIContext, CLIError
from starter_cli.cli.console import console
from starter_cli.cli.env import EnvFile
from starter_cli.cli.infra_commands import DependencyStatus
from starter_cli.cli.setup.automation import AutomationState
from starter_cli.cli.setup.inputs import InputProvider
from starter_cli.cli.verification import (
    VerificationArtifact,
    append_verification_artifact,
    load_verification_artifacts,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from starter_cli.cli.setup.infra import InfraSession

FRONTEND_ENV_RELATIVE = Path("agent-next-15-frontend/.env.local")


@dataclass(slots=True)
class WizardContext:
    """Mutable state shared across wizard sections."""

    cli_ctx: CLIContext
    profile: str
    backend_env: EnvFile
    frontend_env: EnvFile | None
    frontend_path: Path | None
    api_base_url: str = "http://127.0.0.1:8000"
    is_headless: bool = False
    summary_path: Path | None = None
    markdown_summary_path: Path | None = None
    dependency_statuses: list[DependencyStatus] = field(default_factory=list)
    automation: AutomationState = field(default_factory=AutomationState)
    infra_session: "InfraSession | None" = None
    verification_artifacts: list[VerificationArtifact] = field(default_factory=list)
    verification_log_path: Path = field(init=False)
    historical_verifications: list[VerificationArtifact] = field(init=False)

    def __post_init__(self) -> None:
        self.verification_log_path = (
            self.cli_ctx.project_root / "var/reports/verification-artifacts.json"
        )
        self.historical_verifications = load_verification_artifacts(self.verification_log_path)

    # ------------------------------------------------------------------
    # Env helpers
    # ------------------------------------------------------------------
    def current(self, key: str) -> str | None:
        return self.backend_env.get(key) or os.environ.get(key)

    def current_bool(self, key: str, default: bool = False) -> bool:
        value = self.current(key)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "y"}

    def current_frontend_bool(self, key: str, default: bool = False) -> bool:
        if not self.frontend_env:
            return default
        value = self.frontend_env.get(key)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "y"}

    def set_backend(self, key: str, value: str, *, mask: bool = False) -> None:
        self.backend_env.set(key, value)
        os.environ[key] = value
        display = "***" if mask else value
        console.info(f"{key} => {display}", topic="env")

    def unset_backend(self, key: str) -> None:
        self.backend_env.delete(key)
        os.environ.pop(key, None)
        console.info(f"{key} => <removed>", topic="env")

    def set_backend_bool(self, key: str, value: bool) -> None:
        self.set_backend(key, "true" if value else "false")

    def set_frontend(self, key: str, value: str) -> None:
        if not self.frontend_env:
            return
        self.frontend_env.set(key, value)
        console.info(f"[frontend] {key} => {value}", topic="env")

    def set_frontend_bool(self, key: str, value: bool) -> None:
        self.set_frontend(key, "true" if value else "false")

    def ensure_secret(
        self,
        provider: InputProvider,
        *,
        key: str,
        label: str,
        length: int = 32,
    ) -> None:
        existing = self.current(key)
        placeholders = {
            "",
            "change-me",
            "change-me-too",
            "change-me-again",
            "change-me-email",
            "change-me-reset",
        }
        if existing and existing not in placeholders:
            self.set_backend(key, existing, mask=True)
            return
        console.info(f"{label} is not set; leave blank to autogenerate.", topic="wizard")
        value = provider.prompt_secret(
            key=key,
            prompt=label,
            existing=None,
            required=False,
        )
        if not value:
            value = secrets.token_urlsafe(length)
            console.info(f"Generated random value for {key}", topic="wizard")
        self.set_backend(key, value, mask=True)

    def require_env(self, key: str) -> str:
        value = self.current(key)
        if not value:
            raise CLIError(f"{key} must be set before continuing.")
        return value

    # ------------------------------------------------------------------
    # Side effects
    # ------------------------------------------------------------------
    def save_env_files(self) -> None:
        self.backend_env.save()
        console.success("Updated .env.local", topic="wizard")
        if self.frontend_env:
            self.frontend_env.save()
            console.success("Updated agent-next-15-frontend/.env.local", topic="wizard")
        elif self.frontend_path:
            console.warn(
                "Frontend directory missing; skipped agent-next-15-frontend/.env.local.",
                topic="wizard",
            )

    def load_environment(self) -> None:
        self.cli_ctx.load_environment(verbose=False)

    def refresh_settings_cache(self) -> None:
        self.cli_ctx.settings = None
        try:
            cache_clear = get_settings.cache_clear
        except AttributeError:  # pragma: no cover - defensive
            return
        cache_clear()

    def optional_settings(self):  # pragma: no cover - passthrough
        return self.cli_ctx.optional_settings()

    def env_snapshot(self) -> dict[str, str]:
        return dict(os.environ)

    def run_subprocess(self, cmd: list[str], *, topic: str, check: bool = True) -> None:
        console.info(" ".join(cmd), topic=topic)
        subprocess.run(cmd, check=check, cwd=self.cli_ctx.project_root)

    def run_migrations(self) -> None:
        self.run_subprocess(["make", "migrate"], topic="migrate")

    def record_verification(
        self,
        *,
        provider: str,
        identifier: str,
        status: str,
        detail: str | None = None,
        source: str = "wizard",
    ) -> VerificationArtifact:
        artifact = VerificationArtifact(
            provider=provider,
            identifier=identifier,
            status=status,
            detail=detail,
            source=source,
        )
        self.verification_artifacts.append(artifact)
        self.historical_verifications.append(artifact)
        append_verification_artifact(self.verification_log_path, artifact)
        return artifact


def build_env_files(cli_ctx: CLIContext) -> tuple[EnvFile, EnvFile | None, Path | None]:
    backend_path = cli_ctx.project_root / ".env.local"
    backend_path.parent.mkdir(parents=True, exist_ok=True)
    backend_env = EnvFile(backend_path)

    frontend_path = cli_ctx.project_root / FRONTEND_ENV_RELATIVE
    if frontend_path.parent.exists():
        frontend_env: EnvFile | None = EnvFile(frontend_path)
    else:
        frontend_env = None

    return backend_env, frontend_env, frontend_path


__all__ = ["WizardContext", "build_env_files", "FRONTEND_ENV_RELATIVE"]
