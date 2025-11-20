from __future__ import annotations

import asyncio
import sys
from importlib import import_module
from uuid import uuid4
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIError

from .automation import AutomationPhase, AutomationStatus

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ._wizard.context import WizardContext


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


def _ensure_import_paths(project_root: Path) -> None:
    if project_root.as_posix() not in sys.path:
        sys.path.insert(0, project_root.as_posix())
    backend_root = project_root / "api-service"
    if backend_root.as_posix() not in sys.path:
        sys.path.insert(0, backend_root.as_posix())


async def _seed_dev_user(config: DevUserConfig):
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    password_module = import_module("app.core.password_policy")
    security_module = import_module("app.core.security")
    db_engine_module = import_module("app.infrastructure.db.engine")
    auth_models = import_module("app.infrastructure.persistence.auth.models")
    conv_models = import_module("app.infrastructure.persistence.conversations.models")

    PasswordPolicyError = getattr(password_module, "PasswordPolicyError")
    validate_password_strength = getattr(password_module, "validate_password_strength")
    PASSWORD_HASH_VERSION = getattr(security_module, "PASSWORD_HASH_VERSION")
    get_password_hash = getattr(security_module, "get_password_hash")
    get_async_sessionmaker = getattr(db_engine_module, "get_async_sessionmaker")
    init_engine = getattr(db_engine_module, "init_engine")
    PasswordHistory = getattr(auth_models, "PasswordHistory")
    TenantUserMembership = getattr(auth_models, "TenantUserMembership")
    UserAccount = getattr(auth_models, "UserAccount")
    UserProfile = getattr(auth_models, "UserProfile")
    UserStatus = getattr(auth_models, "UserStatus")
    TenantAccount = getattr(conv_models, "TenantAccount")

    await init_engine(run_migrations=False)
    sessionmaker = get_async_sessionmaker()

    async with sessionmaker() as session:
        assert isinstance(session, AsyncSession)

        result = await session.execute(
            select(UserAccount).where(UserAccount.email == config.email)
        )
        existing = result.scalars().first()
        if existing:
            return "exists"

        try:
            validate_password_strength(config.password, user_inputs=[config.email])
        except PasswordPolicyError as exc:
            raise CLIError(str(exc)) from exc

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


def seed_dev_user(context: "WizardContext", config: DevUserConfig) -> str:
    _ensure_import_paths(context.cli_ctx.project_root)
    try:
        get_settings = getattr(import_module("app.core.config"), "get_settings")
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise CLIError(
            "Unable to import backend modules. Ensure api-service is on PYTHONPATH or run the CLI "
            "from the repository root."
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
    )

    try:
        result = asyncio.run(_seed_dev_user(config))
    except CLIError:
        raise
    except Exception as exc:  # pragma: no cover - runtime failures
        raise CLIError(f"Failed to seed dev user: {exc}") from exc

    if result == "exists":
        console.info(
            f"Dev user {config.email} already exists; skipping seeding.",
            topic="dev-user",
        )
    else:
        console.success(
            f"Seeded dev user {config.email} in tenant {config.tenant_slug}.",
            topic="dev-user",
        )
        if config.generated_password:
            console.warn(
                f"Generated password (copy now, not stored anywhere): {config.password}",
                topic="dev-user",
            )
        else:
            console.info("Password provided via wizard; not persisted to disk.", topic="dev-user")
    return result or "unknown"


def run_dev_user_automation(context: "WizardContext") -> None:
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

    if context.dev_user_config is None:
        context.automation.update(
            AutomationPhase.DEV_USER,
            AutomationStatus.SKIPPED,
            "Dev user prompts were not completed.",
        )
        context.refresh_automation_ui(AutomationPhase.DEV_USER)
        return

    context.automation.update(
        AutomationPhase.DEV_USER,
        AutomationStatus.RUNNING,
        "Seeding dev user.",
    )
    context.refresh_automation_ui(AutomationPhase.DEV_USER)

    try:
        result = seed_dev_user(context, context.dev_user_config)
    except CLIError as exc:
        context.automation.update(
            AutomationPhase.DEV_USER,
            AutomationStatus.FAILED,
            f"Dev user seeding failed: {exc}",
        )
        context.refresh_automation_ui(AutomationPhase.DEV_USER)
        console.error(f"Dev user seeding failed: {exc}", topic="dev-user")
        return

    note = "Dev user exists; left untouched." if result == "exists" else "Dev user seeded."
    context.automation.update(
        AutomationPhase.DEV_USER,
        AutomationStatus.SUCCEEDED,
        note,
    )
    context.refresh_automation_ui(AutomationPhase.DEV_USER)
    if result != "exists":
        console.section("Dev User Ready", "Use these credentials to sign in locally.")
        console.info(f"Email: {context.dev_user_config.email}", topic="dev-user")
        console.info(
            f"Tenant: {context.dev_user_config.tenant_slug} ({context.dev_user_config.tenant_name})",
            topic="dev-user",
        )
        console.info(f"Role: {context.dev_user_config.role}", topic="dev-user")
        if context.dev_user_config.generated_password:
            console.warn(
                f"Password (copy now, not stored): {context.dev_user_config.password}",
                topic="dev-user",
            )
        else:
            console.info("Password provided during wizard.", topic="dev-user")


__all__ = ["DevUserConfig", "seed_dev_user", "run_dev_user_automation"]
