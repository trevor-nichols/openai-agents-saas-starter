from __future__ import annotations

import json
from pathlib import Path

from starter_console.core import CLIContext

from .._wizard import audit
from .._wizard.context import WizardContext
from .._wizard.snapshot import write_snapshot_and_diff
from ..automation import AutomationPhase, AutomationStatus
from ..dev_user import run_dev_user_automation
from ..infra import InfraSession
from ..tenant_summary import capture_tenant_summary
from .sources import collect_sections, load_setting_descriptions


def apply_and_save(
    ctx: CLIContext,
    *,
    profile_id: str,
    profiles_path: Path | None,
    answers: dict[str, str],
    summary_path: Path | None,
    markdown_summary_path: Path | None,
    export_answers_path: Path | None,
    output_format: str,
    run_automation: bool,
) -> None:
    descriptions = load_setting_descriptions(ctx.project_root)
    _, wizard_ctx = collect_sections(
        ctx,
        profile_id=profile_id,
        profiles_path=profiles_path,
        answers=answers,
        descriptions=descriptions,
        dry_run=False,
    )
    wizard_ctx.summary_path = summary_path
    wizard_ctx.markdown_summary_path = markdown_summary_path

    wizard_ctx.save_env_files()
    wizard_ctx.load_environment()
    wizard_ctx.refresh_settings_cache()
    capture_tenant_summary(wizard_ctx)

    sections = audit.build_sections(wizard_ctx)
    audit.render_sections(wizard_ctx, output_format=output_format, sections=sections)
    audit.render_schema_summary(wizard_ctx)
    audit.write_summary(wizard_ctx, sections)
    audit.write_markdown_summary(wizard_ctx, sections)
    write_snapshot_and_diff(wizard_ctx)

    if export_answers_path:
        export_answers_path.parent.mkdir(parents=True, exist_ok=True)
        export_answers_path.write_text(json.dumps(answers, indent=2), encoding="utf-8")
        wizard_ctx.console.success(
            f"Wrote prompt answers to {export_answers_path}",
            topic="wizard",
        )

    if run_automation:
        _run_automation(
            wizard_ctx,
            profile_id=profile_id,
            profiles_path=profiles_path,
            answers=answers,
        )


def _run_automation(
    wizard_ctx: WizardContext,
    *,
    profile_id: str,
    profiles_path: Path | None,
    answers: dict[str, str],
) -> None:
    def _request_phase(phase: AutomationPhase) -> None:
        allowed = wizard_ctx.policy_automation_allowed(phase)
        wizard_ctx.automation.request(phase, enabled=allowed)

    _request_phase(AutomationPhase.INFRA)
    _request_phase(AutomationPhase.MIGRATIONS)
    _request_phase(AutomationPhase.DEV_USER)

    infra = InfraSession(wizard_ctx)
    wizard_ctx.infra_session = infra
    infra.ensure_compose()

    if wizard_ctx.current_bool("VAULT_VERIFY_ENABLED", False):
        wizard_ctx.automation.request(
            AutomationPhase.SECRETS,
            enabled=wizard_ctx.policy_automation_allowed(AutomationPhase.SECRETS),
        )
        infra.ensure_vault(enabled=True)

    migrations_record = wizard_ctx.automation.get(AutomationPhase.MIGRATIONS)
    if migrations_record.enabled:
        wizard_ctx.automation.update(
            AutomationPhase.MIGRATIONS,
            AutomationStatus.RUNNING,
            "Running `just migrate`.",
        )
        try:
            wizard_ctx.run_migrations()
        except Exception as exc:  # pragma: no cover - runtime failure path
            wizard_ctx.automation.update(
                AutomationPhase.MIGRATIONS,
                AutomationStatus.FAILED,
                f"Migrations failed: {exc}",
            )
        else:
            wizard_ctx.automation.update(
                AutomationPhase.MIGRATIONS,
                AutomationStatus.SUCCEEDED,
                "Database migrated.",
            )

    run_dev_user_automation(wizard_ctx)

    infra.keep_compose_active = True


__all__ = ["apply_and_save"]
