from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime

from starter_cli.core.inventory import WIZARD_PROMPTED_ENV_VARS
from starter_cli.telemetry import artifacts_to_dict

from ..models import CheckResult, SectionResult
from .context import WizardContext


def build_sections(context: WizardContext) -> list[SectionResult]:
    settings = context.cli_ctx.optional_settings()
    env_snapshot = context.env_snapshot()
    return [
        _secrets_section(context.profile, settings, env_snapshot),
        _providers_section(context, settings, env_snapshot),
        _tenant_observability_section(env_snapshot),
        _signup_worker_section(settings, env_snapshot),
    ]


def render_sections(
    context: WizardContext,
    *,
    output_format: str,
    sections: Sequence[SectionResult],
) -> str | None:
    if output_format == "json":
        payload = [
            {
                "milestone": section.milestone,
                "focus": section.focus,
                "status": section.overall_status,
                "checks": [
                    {
                        "name": check.name,
                        "status": check.status,
                        "required": check.required,
                        "detail": check.detail,
                    }
                    for check in section.checks
                ],
            }
            for section in sections
        ]
        text = json.dumps(payload, indent=2)
        print(text)
        return text
    if output_format == "checklist":
        text = _build_checklist_markdown(context, sections)
        context.console.stream.write(text + "\n")
        return text

    context.console.info(f"Profile: {context.profile}")
    if context.cli_ctx.loaded_env_files:
        context.console.info(
            "Loaded env files: "
            + ", ".join(str(path) for path in context.cli_ctx.loaded_env_files),
            topic="env",
        )
    else:
        context.console.warn("No env files loaded. Provide values via --env-file or environment.")

    for section in sections:
        context.console.newline()
        context.console.info(f"{section.milestone} — {section.focus}")
        for check in section.checks:
            detail = f" ({check.detail})" if check.detail else ""
            context.console.info(f"- {check.name}: {check.status}{detail}")
    return None


def render_schema_summary(context: WizardContext) -> None:
    settings = context.cli_ctx.optional_settings()
    if not settings:
        context.console.warn(
            "Unable to load settings for inventory summary; run `starter_cli config dump-schema` "
            "manually.",
            topic="wizard",
        )
        return
    fields = getattr(settings.__class__, "model_fields", {})
    aliases = {(field.alias or name).upper() for name, field in fields.items()}
    wizard_coverage = len(aliases & WIZARD_PROMPTED_ENV_VARS)
    total = len(aliases)
    remaining = sorted(aliases - WIZARD_PROMPTED_ENV_VARS)
    context.console.info(
        f"Wizard prompts now cover {wizard_coverage}/{total} backend env vars.",
        topic="wizard",
    )
    if remaining:
        preview = ", ".join(remaining[:5])
        suffix = " …" if len(remaining) > 5 else ""
        context.console.info(
            "Review remaining variables via `starter_cli config dump-schema` or "
            f"docs/trackers/CLI_ENV_INVENTORY.md (next: {preview}{suffix}).",
            topic="wizard",
        )


def write_summary(context: WizardContext, sections: list[SectionResult]) -> None:
    if not context.summary_path:
        return
    summary = {
        "profile": context.profile,
        "hosting_preset": context.hosting_preset,
        "cloud_provider": context.cloud_provider,
        "show_advanced_prompts": context.show_advanced_prompts,
        "api_base_url": context.api_base_url,
        "backend_env_path": str(context.backend_env.path),
        "frontend_env_path": str(context.frontend_path) if context.frontend_path else None,
        "current_run_verification_artifacts": artifacts_to_dict(context.verification_artifacts),
        "verification_artifacts": artifacts_to_dict(context.historical_verifications),
        "tenant_summary": context.tenant_summary.as_dict() if context.tenant_summary else None,
        "milestones": [
            {
                "milestone": section.milestone,
                "focus": section.focus,
                "status": section.overall_status,
                "checks": [
                    {
                        "name": check.name,
                        "status": check.status,
                        "required": check.required,
                        "detail": check.detail,
                    }
                    for check in section.checks
                ],
            }
            for section in sections
        ],
    }
    context.summary_path.parent.mkdir(parents=True, exist_ok=True)
    context.summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    context.console.success(f"Summary written to {context.summary_path}", topic="wizard")


def write_markdown_summary(context: WizardContext, sections: list[SectionResult]) -> None:
    path = context.markdown_summary_path
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# One-Stop Setup Summary")
    lines.append("")
    lines.append(f"- **Profile**: `{context.profile}`")
    if context.hosting_preset:
        lines.append(f"- **Hosting preset**: `{context.hosting_preset}`")
    if context.cloud_provider:
        lines.append(f"- **Cloud provider**: `{context.cloud_provider}`")
    lines.append(f"- **Advanced prompts**: `{context.show_advanced_prompts}`")
    lines.append(f"- **API Base URL**: `{context.api_base_url}`")
    lines.append(
        f"- **Backend env**: `{context.backend_env.path}`"
        + (f" — Frontend: `{context.frontend_path}`" if context.frontend_path else "")
    )
    lines.append("")
    lines.append("## Automation Status")
    lines.append("")
    lines.append("| Phase | Status | Note |")
    lines.append("| --- | --- | --- |")
    if context.automation.records:
        for phase, record in context.automation.records.items():
            note = record.note or ""
            lines.append(f"| {phase.value} | {record.status.value} | {note} |")
    else:
        lines.append("| _none_ | — | — |")
    lines.append("")
    if context.tenant_summary:
        lines.append("## Tenant Summary")
        lines.append("")
        tenant = context.tenant_summary
        lines.append(f"- Slug: `{tenant.slug}`")
        lines.append(f"- Tenant ID: `{tenant.tenant_id}`")
        if tenant.name:
            lines.append(f"- Name: `{tenant.name}`")
        if tenant.created_at:
            lines.append(f"- Created at: `{tenant.created_at}`")
        lines.append("")
    lines.append("## Current Verification Artifacts")
    lines.append("")
    artifacts = context.verification_artifacts or []
    if artifacts:
        for artifact in artifacts:
            detail = f" — {artifact.detail}" if artifact.detail else ""
            lines.append(
                f"- **{artifact.provider}** `{artifact.identifier}` → {artifact.status}{detail}"
            )
    else:
        lines.append("No verification artifacts recorded in this run.")
    lines.append("")
    lines.append(
        "_Full ledger saved to_ "
        f"`{context.verification_log_path}`"
    )
    lines.append("")
    lines.append("## Milestones")
    lines.append("")
    lines.append("| Milestone | Status | Focus |")
    lines.append("| --- | --- | --- |")
    for section in sections:
        lines.append(f"| {section.milestone} | {section.overall_status} | {section.focus} |")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    context.console.success(f"Markdown summary written to {path}", topic="wizard")


def _secrets_section(profile: str, settings, env_snapshot: dict[str, str]) -> SectionResult:
    section = SectionResult("M1 - Secrets & Key Management", "Rotate and harden keys.")
    password_pepper = env_snapshot.get("AUTH_PASSWORD_PEPPER")
    refresh_pepper = env_snapshot.get("AUTH_REFRESH_TOKEN_PEPPER")

    section.checks.append(_pepper_status("AUTH_PASSWORD_PEPPER", password_pepper))
    section.checks.append(_pepper_status("AUTH_REFRESH_TOKEN_PEPPER", refresh_pepper))

    vault_required = profile in {"staging", "production"}
    section.checks.extend(
        [
            _env_presence("VAULT_ADDR", env_snapshot, required=vault_required),
            _env_presence("VAULT_TOKEN", env_snapshot, required=vault_required),
            _env_presence("VAULT_TRANSIT_KEY", env_snapshot, required=vault_required),
        ]
    )

    if settings:
        warnings = settings.secret_warnings()
        if warnings:
            section.checks.append(
                CheckResult(
                    name="secret_warnings",
                    status="warning",
                    required=True,
                    detail="; ".join(warnings),
                )
            )
        else:
            section.checks.append(
                CheckResult(
                    name="secret_warnings",
                    status="ok",
                    required=False,
                    detail="All managed secrets overridden.",
                )
            )
    else:
        section.checks.append(
            CheckResult(
                name="secret_warnings",
                status="pending",
                required=True,
                detail="Unable to load settings; verify .env completeness.",
            )
        )
    return section


def _providers_section(
    context: WizardContext,
    settings,
    env_snapshot: dict[str, str],
) -> SectionResult:
    section = SectionResult(
        "M2 - Provider & Infra Provisioning",
        "Validate third-party credentials & database.",
    )
    section.checks.extend(
        [
            _env_presence("OPENAI_API_KEY", env_snapshot),
            _env_presence("STRIPE_SECRET_KEY", env_snapshot),
            _env_presence("STRIPE_WEBHOOK_SECRET", env_snapshot),
            _env_presence("RESEND_API_KEY", env_snapshot, required=False),
            _env_presence("DATABASE_URL", env_snapshot, required=False),
            _env_presence("REDIS_URL", env_snapshot),
            _env_presence("RATE_LIMIT_REDIS_URL", env_snapshot, required=False),
            _env_presence("AUTH_CACHE_REDIS_URL", env_snapshot, required=False),
            _env_presence("SECURITY_TOKEN_REDIS_URL", env_snapshot, required=False),
            _env_presence("BILLING_EVENTS_REDIS_URL", env_snapshot, required=False),
        ]
    )

    if settings and getattr(settings, "stripe_product_price_map", None):
        section.checks.append(
            CheckResult(
                name="stripe_plan_map",
                status="ok",
                required=False,
                detail="Plan map configured.",
            )
        )
    else:
        section.checks.append(
            CheckResult(
                name="stripe_plan_map",
                status="missing",
                required=False,
                detail="Review STRIPE_PRODUCT_PRICE_MAP.",
            )
        )
    stripe_artifact = _latest_artifact(context, provider="stripe")
    if stripe_artifact:
        section.checks.append(
            CheckResult(
                name="stripe_automation",
                status="ok" if stripe_artifact.status == "passed" else "warning",
                required=False,
                detail=stripe_artifact.detail or stripe_artifact.identifier,
            )
        )
    return section


def _tenant_observability_section(env_snapshot: dict[str, str]) -> SectionResult:
    section = SectionResult(
        "M3 - Tenant & Observability",
        "Baseline tenant + logging + geo telemetry.",
    )
    section.checks.extend(
        [
            _env_presence("TENANT_DEFAULT_SLUG", env_snapshot),
            _env_presence("LOGGING_SINKS", env_snapshot),
            _env_presence("GEOIP_PROVIDER", env_snapshot),
        ]
    )
    return section


def _signup_worker_section(settings, env_snapshot: dict[str, str]) -> SectionResult:
    section = SectionResult(
        "M4 - Signup & Worker policy",
        "Ensure signup controls & billing workers match deployment.",
    )
    section.checks.extend(
        [
            _env_presence("SIGNUP_ACCESS_POLICY", env_snapshot),
            _env_presence("ALLOW_PUBLIC_SIGNUP", env_snapshot),
            _env_presence("SIGNUP_RATE_LIMIT_PER_HOUR", env_snapshot),
            _env_presence("SIGNUP_RATE_LIMIT_PER_IP_DAY", env_snapshot),
            _env_presence("SIGNUP_RATE_LIMIT_PER_EMAIL_DAY", env_snapshot),
            _env_presence("SIGNUP_RATE_LIMIT_PER_DOMAIN_DAY", env_snapshot),
            _env_presence("SIGNUP_CONCURRENT_REQUESTS_LIMIT", env_snapshot),
            _env_presence("SIGNUP_DEFAULT_TRIAL_DAYS", env_snapshot),
            _env_presence("BILLING_RETRY_DEPLOYMENT_MODE", env_snapshot),
        ]
    )

    if settings:
        worker_enabled = getattr(settings, "enable_billing_retry_worker", None)
        deployment_mode = getattr(settings, "billing_retry_deployment_mode", None)
        detail = None
        status = "pending"
        if worker_enabled is not None:
            if deployment_mode == "dedicated" and not worker_enabled:
                detail = "dedicated (disabled on API pod)"
                status = "ok"
            else:
                detail = "inline" if worker_enabled else "disabled"
                status = "ok"
        section.checks.append(
            CheckResult(
                name="retry_worker",
                status=status,
                detail=detail,
            )
        )
    else:
        section.checks.append(
            CheckResult(
                name="retry_worker",
                status="pending",
                detail="Need settings to inspect ENABLE_BILLING_RETRY_WORKER.",
            )
        )
    return section


def _latest_artifact(
    context: WizardContext,
    *,
    provider: str,
):
    combined = context.verification_artifacts + context.historical_verifications
    for artifact in reversed(combined):
        if artifact.provider == provider:
            return artifact
    return None


def _env_presence(key: str, env: dict[str, str], *, required: bool = True) -> CheckResult:
    status = "ok" if env.get(key) else "missing"
    return CheckResult(name=key, status=status, required=required)


def _pepper_status(key: str, value: str | None) -> CheckResult:
    if not value:
        return CheckResult(name=key, status="missing")
    placeholders = {"change-me", "change-me-too", "change-me-again"}
    if value in placeholders:
        return CheckResult(name=key, status="warning", detail="Using starter value")
    return CheckResult(name=key, status="ok")


_STATUS_EMOJI = {
    "ok": "✅",
    "missing": "❌",
    "warning": "⚠️",
    "pending": "⏳",
    "action_required": "❗",
}


def _build_checklist_markdown(
    context: WizardContext,
    sections: Sequence[SectionResult],
) -> str:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S %Z")
    env_files = context.cli_ctx.loaded_env_files
    env_file_line = (
        ", ".join(f"`{path}`" for path in env_files)
        if env_files
        else "_(none loaded via --env-file)_"
    )
    lines: list[str] = []
    lines.append("# Starter CLI Setup Checklist")
    lines.append("")
    lines.append(f"- Profile: `{context.profile}`")
    lines.append(f"- Generated: {timestamp}")
    lines.append(f"- Loaded env files: {env_file_line}")
    lines.append("- Tracker reference: `docs/trackers/complete/MILESTONE_TRACKER.md`")
    lines.append(
        "- Regenerate: `python -m starter_cli.app setup wizard --profile "
        f"{context.profile} --report-only --output checklist --markdown-summary-path <path>`"
    )
    lines.append("")
    for section in sections:
        lines.append(f"## {section.milestone}")
        lines.append(section.focus)
        lines.append("")
        for check in section.checks:
            lines.append(_format_check_entry(check))
        lines.append("")
    return "\n".join(lines).strip()


def _format_check_entry(check: CheckResult) -> str:
    checkbox = "x" if check.status == "ok" else " "
    emoji = _STATUS_EMOJI.get(check.status, "")
    optional = " _(optional)_" if not check.required else ""
    detail = f" — {check.detail}" if check.detail else ""
    status = check.status.replace("_", " ")
    status_fragment = f"{emoji} {status}".strip()
    return f"- [{checkbox}] `{check.name}`{optional} — {status_fragment}{detail}"


__all__ = ["build_sections", "render_sections", "render_schema_summary", "write_summary"]
