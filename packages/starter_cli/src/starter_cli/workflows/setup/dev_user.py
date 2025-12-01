from __future__ import annotations

import asyncio
import json
import secrets
import sys
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIError

from .automation import AutomationPhase, AutomationStatus

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ._wizard.context import WizardContext


# Defaults that match the marketing promise: one-command local setup.
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


def _ensure_import_paths(project_root: Path) -> None:
    # Keep backend importable without requiring PYTHONPATH tweaks.
    if project_root.as_posix() not in sys.path:
        sys.path.insert(0, project_root.as_posix())
    backend_root = project_root / "apps" / "api-service"
    if backend_root.as_posix() not in sys.path:
        sys.path.insert(0, backend_root.as_posix())


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


async def _seed_dev_user(config: DevUserConfig) -> str:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    password_module = import_module("app.core.password_policy")
    security_module = import_module("app.core.security")
    db_engine_module = import_module("app.infrastructure.db.engine")
    auth_models = import_module("app.infrastructure.persistence.auth.models")
    # Import related models to satisfy relationship registrations on TenantAccount.
    import_module("app.infrastructure.persistence.billing.models")
    import_module("app.infrastructure.persistence.tenants.models")
    conv_models = import_module("app.infrastructure.persistence.conversations.models")

    PasswordPolicyError = password_module.PasswordPolicyError
    validate_password_strength = password_module.validate_password_strength
    PASSWORD_HASH_VERSION = security_module.PASSWORD_HASH_VERSION
    get_password_hash = security_module.get_password_hash
    get_async_sessionmaker = db_engine_module.get_async_sessionmaker
    init_engine = db_engine_module.init_engine
    PasswordHistory = auth_models.PasswordHistory
    TenantUserMembership = auth_models.TenantUserMembership
    UserAccount = auth_models.UserAccount
    UserProfile = auth_models.UserProfile
    UserStatus = auth_models.UserStatus
    TenantAccount = conv_models.TenantAccount

    await init_engine(run_migrations=False)
    sessionmaker = get_async_sessionmaker()

    async with sessionmaker() as session:
        assert isinstance(session, AsyncSession)

        result = await session.execute(select(UserAccount).where(UserAccount.email == config.email))
        existing = result.scalars().first()

        # Always validate the new password so rotations respect the policy.
        try:
            validate_password_strength(config.password, user_inputs=[config.email])
        except PasswordPolicyError as exc:
            raise CLIError(str(exc)) from exc

        if existing:
            if not config.rotate_existing:
                return "exists"

            password_hash = get_password_hash(config.password)
            existing.password_hash = password_hash
            existing.password_pepper_version = PASSWORD_HASH_VERSION
            existing.status = UserStatus.LOCKED if config.locked else UserStatus.ACTIVE

            history = PasswordHistory(
                id=uuid4(),
                user_id=existing.id,
                password_hash=password_hash,
                password_pepper_version=PASSWORD_HASH_VERSION,
            )
            session.add(history)
            await session.commit()
            return "rotated"

        tenant_result = await session.execute(
            select(TenantAccount).where(TenantAccount.slug == config.tenant_slug)
        )
        tenant = tenant_result.scalars().first()
        if tenant is None:
            tenant = TenantAccount(
                id=uuid4(),
                slug=config.tenant_slug,
                name=config.tenant_name,
            )
            session.add(tenant)
            await session.flush()

        password_hash = get_password_hash(config.password)
        user = UserAccount(
            id=uuid4(),
            email=config.email,
            password_hash=password_hash,
            password_pepper_version=PASSWORD_HASH_VERSION,
            status=UserStatus.LOCKED if config.locked else UserStatus.ACTIVE,
        )
        session.add(user)
        await session.flush()

        if config.display_name:
            profile = UserProfile(
                id=uuid4(),
                user_id=user.id,
                display_name=config.display_name,
            )
            session.add(profile)

        membership = TenantUserMembership(
            id=uuid4(),
            user_id=user.id,
            tenant_id=tenant.id,
            role=config.role,
        )
        session.add(membership)

        history = PasswordHistory(
            id=uuid4(),
            user_id=user.id,
            password_hash=password_hash,
            password_pepper_version=PASSWORD_HASH_VERSION,
        )
        session.add(history)

        await session.commit()
        return "created"


def seed_dev_user(context: WizardContext, config: DevUserConfig) -> str:
    _ensure_import_paths(context.cli_ctx.project_root)
    try:
        get_settings = import_module("app.core.settings").get_settings
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise CLIError(
            "Unable to import backend modules. Ensure apps/api-service is on PYTHONPATH "
            "or run the CLI from the repository root."
        ) from exc

    # Validate env is loaded and settings can resolve.
    get_settings()

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
        result = asyncio.run(_seed_dev_user(config))
    except CLIError:
        raise
    except Exception as exc:  # pragma: no cover - runtime failures
        raise CLIError(f"Failed to seed dev user: {exc}") from exc

    return result or "unknown"


def _persist_and_announce(context: WizardContext, config: DevUserConfig, status: str) -> None:
    # Console output (Rich) and plain stdout for shells that suppress styling.
    console.section("Dev User Ready", "Use these credentials to sign in locally.")
    console.info(f"Email: {config.email}", topic="dev-user")
    console.info(
        f"Tenant: {config.tenant_slug} ({config.tenant_name})",
        topic="dev-user",
    )
    console.info(f"Role: {config.role}", topic="dev-user")

    if status in {"created", "rotated"}:
        console.warn(f"Password (copy now, not stored): {config.password}", topic="dev-user")
    else:
        console.info("Password unchanged from previous run (not recoverable).", topic="dev-user")

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
    console.info(
        f"Dev user credentials saved to {path.relative_to(context.cli_ctx.project_root)}",
        topic="dev-user",
    )


def run_dev_user_automation(context: WizardContext) -> None:
    record = context.automation.get(AutomationPhase.DEV_USER)
    if not record.enabled:
        return
    if record.status == AutomationStatus.BLOCKED:
        console.warn(record.note or "Dev user automation blocked.", topic="dev-user")
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
        console.warn(
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
        console.error(f"Dev user seeding failed: {exc}", topic="dev-user")
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
