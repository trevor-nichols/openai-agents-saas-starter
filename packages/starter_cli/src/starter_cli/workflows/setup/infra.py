from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

from starter_cli.core import CLIError

from .automation import AutomationPhase, AutomationStatus

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from ._wizard.context import WizardContext


@dataclass(slots=True)
class InfraSession:
    context: WizardContext
    compose_started: bool = False
    vault_started: bool = False
    keep_compose_active: bool = False

    def ensure_compose(self) -> None:
        record = self.context.automation.get(AutomationPhase.INFRA)
        if not record.enabled or record.status not in {
            AutomationStatus.PENDING,
            AutomationStatus.RUNNING,
        }:
            return
        note = "Starting Docker compose stack (Postgres + Redis)"
        self.context.automation.update(AutomationPhase.INFRA, AutomationStatus.RUNNING, note)
        self.context.refresh_automation_ui(AutomationPhase.INFRA)
        self.context.console.info(note, topic="infra")
        try:
            self._run_cli(["infra", "compose", "up"])
        except (subprocess.CalledProcessError, CLIError) as exc:
            self._handle_failure(
                phase=AutomationPhase.INFRA,
                message="Docker compose automation failed",
                error=exc,
                log_command=["infra", "compose", "logs"],
            )
            raise CLIError("Failed to start Docker compose stack; see logs above.") from exc
        else:
            self.compose_started = True
            self.context.automation.update(
                AutomationPhase.INFRA,
                AutomationStatus.SUCCEEDED,
                "Docker compose stack running.",
            )
            self.context.refresh_automation_ui(AutomationPhase.INFRA)
            self.context.console.success("Docker compose stack is running.", topic="infra")

    def ensure_vault(self, enabled: bool) -> None:
        record = self.context.automation.get(AutomationPhase.SECRETS)
        if not record.enabled:
            return
        if not enabled:
            self.context.automation.update(
                AutomationPhase.SECRETS,
                AutomationStatus.SKIPPED,
                "Vault automation skipped (verification disabled).",
            )
            return
        if self.context.profile != "demo":
            self.context.automation.update(
                AutomationPhase.SECRETS,
                AutomationStatus.BLOCKED,
                "Vault automation only supported for demo profile.",
            )
            return
        if record.status not in {AutomationStatus.PENDING, AutomationStatus.RUNNING}:
            return
        note = "Starting Vault dev signer via docker compose"
        self.context.automation.update(AutomationPhase.SECRETS, AutomationStatus.RUNNING, note)
        self.context.refresh_automation_ui(AutomationPhase.SECRETS)
        self.context.console.info(note, topic="vault")
        try:
            self._run_cli(["infra", "vault", "up"], topic="vault")
        except (subprocess.CalledProcessError, CLIError) as exc:
            self._handle_failure(
                phase=AutomationPhase.SECRETS,
                message="Vault automation failed",
                error=exc,
                log_command=["infra", "vault", "logs"],
                topic="vault",
            )
            raise CLIError("Failed to start Vault dev signer; see logs above.") from exc
        else:
            self.vault_started = True
            self.context.automation.update(
                AutomationPhase.SECRETS,
                AutomationStatus.SUCCEEDED,
                "Vault dev signer ready.",
            )
            self.context.refresh_automation_ui(AutomationPhase.SECRETS)
            self.context.console.success(
                "Vault dev signer ready at VAULT_DEV_HOST_ADDR.",
                topic="vault",
            )

    def cleanup(self) -> None:
        if self.vault_started:
            self.context.console.info("Stopping Vault dev signer …", topic="vault")
            self._safe_shutdown(["infra", "vault", "down"], topic="vault")
        if self.compose_started and not self.keep_compose_active:
            self.context.console.info("Stopping Docker compose stack …", topic="infra")
            self._safe_shutdown(["infra", "compose", "down"], topic="infra")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _run_cli(self, args: list[str], *, topic: str = "infra") -> None:
        cmd = ["python", "-m", "starter_cli.app", *args]
        self.context.run_subprocess(cmd, topic=topic)

    def _safe_shutdown(self, args: list[str], *, topic: str) -> None:
        try:
            self._run_cli(args, topic=topic)
        except Exception as exc:  # pragma: no cover - best effort
            self.context.console.warn(f"Failed to run {' '.join(args)}: {exc}", topic=topic)

    def _handle_failure(
        self,
        *,
        phase: AutomationPhase,
        message: str,
        error: Exception,
        log_command: list[str],
        topic: str = "infra",
    ) -> None:
        self.context.console.error(f"{message}: {error}", topic=topic)
        self.context.automation.update(phase, AutomationStatus.FAILED, f"{message}: {error}")
        self.context.refresh_automation_ui(phase)
        try:
            self._run_cli(log_command, topic=topic)
        except Exception:  # pragma: no cover - best effort
            self.context.console.warn("Unable to capture logs after failure.", topic=topic)


__all__ = ["InfraSession"]
