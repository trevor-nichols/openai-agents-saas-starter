from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from starter_cli.core import CLIError
from starter_cli.services.backend_scripts import (
    extract_json_payload,
    run_backend_script,
)

from .automation import AutomationPhase, AutomationStatus

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ._wizard.context import WizardContext


# Defaults that match the marketing promise: one-command demo setup.
DEFAULT_EMAIL = "dev@example.com"
DEFAULT_NAME = "Dev Admin"
DEFAULT_TENANT = "default"
DEFAULT_TENANT_NAME = "Default Tenant"
DEFAULT_ROLE = "admin"


@dataclass(slots=True)
class DevUserConfig:
    email: str
    password: str
    tenant_slug: str
    tenant_name: str
    role: str
    display_name: str = ""
    locked: bool = False
    generated_password: bool = False
    rotate_existing: bool = True


def _resolve_config(context: WizardContext) -> DevUserConfig:
    # If the wizard already captured a config, reuse it. Otherwise synthesize sensible defaults
    # so reruns (or headless runs) still emit credentials.
    if context.dev_user_config:
        return context.dev_user_config

    email = (context.current("DEV_USER_EMAIL") or DEFAULT_EMAIL).strip().lower()
    display_name = (context.current("DEV_USER_DISPLAY_NAME") or DEFAULT_NAME).strip()
    tenant_slug = (context.current("DEV_USER_TENANT_SLUG") or DEFAULT_TENANT).strip()
    tenant_name = (context.current("DEV_USER_TENANT_NAME") or DEFAULT_TENANT_NAME).strip()
    role = (context.current("DEV_USER_ROLE") or DEFAULT_ROLE).strip()
    password = secrets.token_urlsafe(20)

    return DevUserConfig(
        email=email,
        display_name=display_name,
        tenant_slug=tenant_slug,
        tenant_name=tenant_name,
        role=role,
        password=password,
        locked=False,
        generated_password=True,
        rotate_existing=True,
    )


def _run_backend_seed_script(project_root: Path, config: DevUserConfig) -> str:
    cmd_args = [
        "--email",
        config.email,
        "--password",
        config.password,
        "--tenant-slug",
        config.tenant_slug,
        "--tenant-name",
        config.tenant_name,
        "--role",
        config.role,
        "--display-name",
        config.display_name,
    ]
    if config.locked:
        cmd_args.append("--locked")
    if not config.rotate_existing:
        cmd_args.append("--no-rotate-existing")

    completed = run_backend_script(
        project_root=project_root,
        script_name="seed_dev_user.py",
        args=cmd_args,
    )
    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        stdout = (completed.stdout or "").strip()
        detail = stderr or stdout or "unknown error"
        raise CLIError(f"Dev user seeding failed: {detail}")

    payload = extract_json_payload(completed.stdout or "", required_keys=["result"])

    result = payload.get("result")
    if not isinstance(result, str) or not result.strip():
        raise CLIError(f"Dev user seeding returned unexpected payload: {payload}")
    return result


def seed_dev_user(context: WizardContext, config: DevUserConfig) -> str:
    project_root = context.cli_ctx.project_root
    normalized_email = config.email.strip().lower()
    config = DevUserConfig(
        email=normalized_email,
        password=config.password,
        tenant_slug=config.tenant_slug,
        tenant_name=config.tenant_name,
        role=config.role,
        display_name=config.display_name,
        locked=config.locked,
        generated_password=config.generated_password,
        rotate_existing=config.rotate_existing,
    )

    try:
        result = _run_backend_seed_script(project_root, config)
    except CLIError:
        raise
    except Exception as exc:  # pragma: no cover - runtime failures
        raise CLIError(f"Failed to seed dev user: {exc}") from exc

    return result or "unknown"


def _persist_and_announce(context: WizardContext, config: DevUserConfig, status: str) -> None:
    # Console output (Rich) and plain stdout for shells that suppress styling.
    context.console.section("Dev User Ready", "Use these credentials to sign in for the demo.")
    context.console.info(f"Email: {config.email}", topic="dev-user")
    context.console.info(
        f"Tenant: {config.tenant_slug} ({config.tenant_name})",
        topic="dev-user",
    )
    context.console.info(f"Role: {config.role}", topic="dev-user")

    if status in {"created", "rotated"}:
        context.console.warn(
            f"Password (copy now, not stored): {config.password}",
            topic="dev-user",
        )
    else:
        context.console.info(
            "Password unchanged from previous run (not recoverable).",
            topic="dev-user",
        )

    # Plain prints for minimal environments (and for the user transcript).
    print(
        f"[dev-user] email={config.email} tenant={config.tenant_slug} "
        f"role={config.role} status={status}"
    )
    if status in {"created", "rotated"}:
        print(f"[dev-user] password={config.password}")

    # Persist credentials to an artifact so reruns remain discoverable.
    reports_dir = context.cli_ctx.project_root / "var" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / "dev-user-credentials.json"
    payload: dict[str, object] = {
        "email": config.email,
        "tenant": config.tenant_slug,
        "tenant_name": config.tenant_name,
        "role": config.role,
        "status": status,
        "generated_password": config.generated_password,
    }
    if config.display_name:
        payload["display_name"] = config.display_name
    if status in {"created", "rotated"}:
        payload["password"] = config.password

    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    context.console.info(
        f"Dev user credentials saved to {path.relative_to(context.cli_ctx.project_root)}",
        topic="dev-user",
    )


def run_dev_user_automation(context: WizardContext) -> None:
    record = context.automation.get(AutomationPhase.DEV_USER)
    if not record.enabled:
        return
    if record.status == AutomationStatus.BLOCKED:
        context.console.warn(record.note or "Dev user automation blocked.", topic="dev-user")
        context.refresh_automation_ui(AutomationPhase.DEV_USER)
        return

    # If migrations automation was enabled but not successful, block seeding to avoid drift.
    migrations_record = context.automation.get(AutomationPhase.MIGRATIONS)
    if migrations_record.enabled and migrations_record.status not in {
        AutomationStatus.SUCCEEDED,
        AutomationStatus.SKIPPED,
    }:
        context.automation.update(
            AutomationPhase.DEV_USER,
            AutomationStatus.BLOCKED,
            "Dev user seeding waits for migrations to complete.",
        )
        context.refresh_automation_ui(AutomationPhase.DEV_USER)
        context.console.warn(
            "Dev user automation blocked until migrations succeed.",
            topic="dev-user",
        )
        return

    config = _resolve_config(context)
    context.dev_user_config = config

    context.automation.update(
        AutomationPhase.DEV_USER,
        AutomationStatus.RUNNING,
        "Seeding dev user.",
    )
    context.refresh_automation_ui(AutomationPhase.DEV_USER)

    try:
        result = seed_dev_user(context, config)
    except CLIError as exc:
        context.automation.update(
            AutomationPhase.DEV_USER,
            AutomationStatus.FAILED,
            f"Dev user seeding failed: {exc}",
        )
        context.refresh_automation_ui(AutomationPhase.DEV_USER)
        context.console.error(f"Dev user seeding failed: {exc}", topic="dev-user")
        return

    note = {
        "created": "Dev user seeded.",
        "rotated": "Dev user password rotated.",
        "exists": "Dev user exists; password unchanged.",
    }.get(result, "Dev user processed.")

    context.automation.update(
        AutomationPhase.DEV_USER,
        AutomationStatus.SUCCEEDED,
        note,
    )
    context.refresh_automation_ui(AutomationPhase.DEV_USER)

    _persist_and_announce(context, config, result)


__all__ = ["DevUserConfig", "seed_dev_user", "run_dev_user_automation"]
