from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING

from starter_cli.adapters.io.console import console

from .automation import AutomationPhase, AutomationStatus

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ._wizard.context import WizardContext


@dataclass(slots=True)
class DemoTokenConfig:
    account: str
    scopes: list[str]
    tenant_slug: str | None = None
    fingerprint: str | None = None
    force: bool = False


def _ensure_import_paths(project_root: Path) -> None:
    if project_root.as_posix() not in sys.path:
        sys.path.insert(0, project_root.as_posix())
    backend_root = project_root / "api-service"
    if backend_root.as_posix() not in sys.path:
        sys.path.insert(0, backend_root.as_posix())


async def _issue_demo_token(config: DemoTokenConfig, tenant_id: str | None):
    service_accounts = import_module("app.core.service_accounts")
    db_engine = import_module("app.infrastructure.db.engine")
    auth_repo = import_module("app.infrastructure.persistence.auth.repository")
    refresh_mod = import_module("app.services.auth.refresh_token_manager")
    sa_service_mod = import_module("app.services.auth.service_account_service")

    get_default_service_account_registry = service_accounts.get_default_service_account_registry
    init_engine = db_engine.init_engine
    get_refresh_token_repository = auth_repo.get_refresh_token_repository
    RefreshTokenManager = refresh_mod.RefreshTokenManager
    ServiceAccountTokenService = sa_service_mod.ServiceAccountTokenService

    await init_engine(run_migrations=False)
    registry = get_default_service_account_registry()
    refresh_repo = get_refresh_token_repository()
    manager = RefreshTokenManager(refresh_repo)
    service = ServiceAccountTokenService(registry=registry, refresh_tokens=manager)
    return await service.issue_refresh_token(
        account=config.account,
        scopes=config.scopes,
        tenant_id=tenant_id,
        requested_ttl_minutes=None,
        fingerprint=config.fingerprint,
        force=config.force,
    )


def run_demo_token_automation(context: WizardContext) -> None:
    record = context.automation.get(AutomationPhase.DEMO_TOKEN)
    if not record.enabled:
        return
    if record.status == AutomationStatus.BLOCKED:
        console.warn(record.note or "Demo token automation blocked.", topic="demo-token")
        context.refresh_automation_ui(AutomationPhase.DEMO_TOKEN)
        return

    migrations = context.automation.get(AutomationPhase.MIGRATIONS)
    if migrations.enabled and migrations.status not in {
        AutomationStatus.SUCCEEDED,
        AutomationStatus.SKIPPED,
    }:
        context.automation.update(
            AutomationPhase.DEMO_TOKEN,
            AutomationStatus.BLOCKED,
            "Demo token waits for migrations to complete.",
        )
        context.refresh_automation_ui(AutomationPhase.DEMO_TOKEN)
        console.warn("Demo token automation blocked until migrations succeed.", topic="demo-token")
        return

    config = context.demo_token_config or DemoTokenConfig(
        account="demo-bot",
        scopes=["chat:write", "conversations:read"],
        tenant_slug=(context.tenant_summary.slug if context.tenant_summary else None),
        fingerprint="wizard-demo",
        force=False,
    )

    # demo-bot is defined with requires_tenant=false; avoid passing tenant_id to keep
    # issuance valid.
    tenant_id = None

    context.automation.update(
        AutomationPhase.DEMO_TOKEN,
        AutomationStatus.RUNNING,
        "Issuing demo service-account token.",
    )
    context.refresh_automation_ui(AutomationPhase.DEMO_TOKEN)

    _ensure_import_paths(context.cli_ctx.project_root)
    try:
        get_settings = import_module("app.core.config").get_settings
        get_settings()
        result = asyncio.run(_issue_demo_token(config, tenant_id))
    except Exception as exc:  # pragma: no cover - runtime failures
        context.automation.update(
            AutomationPhase.DEMO_TOKEN,
            AutomationStatus.FAILED,
            f"Demo token failed: {exc}",
        )
        context.refresh_automation_ui(AutomationPhase.DEMO_TOKEN)
        console.error(f"Demo token issuance failed: {exc}", topic="demo-token")
        return

    context.automation.update(
        AutomationPhase.DEMO_TOKEN,
        AutomationStatus.SUCCEEDED,
        "Demo token minted.",
    )
    context.refresh_automation_ui(AutomationPhase.DEMO_TOKEN)

    token = result.get("refresh_token") if isinstance(result, dict) else None
    console.section("Demo Token Ready", "Use this refresh token for local testing (not stored).")
    console.warn("Copy this now; it will not be written to disk.", topic="demo-token")
    if token:
        console.info(token, topic="demo-token")
    else:  # pragma: no cover - defensive
        console.warn("Token missing from response.", topic="demo-token")


__all__ = ["DemoTokenConfig", "run_demo_token_automation"]
