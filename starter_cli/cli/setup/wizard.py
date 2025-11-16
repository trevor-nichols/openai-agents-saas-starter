from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from ..common import CLIContext, CLIError
from ..console import console
from ._wizard import audit
from ._wizard.context import FRONTEND_ENV_RELATIVE, WizardContext, build_env_files
from ._wizard.sections import (
    core,
    frontend,
    observability,
    providers,
    secrets,
    security,
    signup,
)
from .automation import ALL_AUTOMATION_PHASES, AutomationPhase
from .infra import InfraSession
from .inputs import InputProvider
from .models import SectionResult
from .preflight import run_preflight
from .tenant_summary import capture_tenant_summary

PROFILE_CHOICES = ("local", "staging", "production")

_AUTOMATION_PROMPTS: dict[AutomationPhase, tuple[str, str, bool]] = {
    AutomationPhase.INFRA: (
        "AUTO_INFRA",
        "Automatically manage Docker compose (Postgres/Redis) and Vault helpers during setup?",
        False,
    ),
    AutomationPhase.SECRETS: (
        "AUTO_SECRETS",
        "Automatically run secrets onboarding flows when credentials are supplied?",
        False,
    ),
    AutomationPhase.STRIPE: (
        "AUTO_STRIPE",
        "Automatically run Stripe provisioning after providers are configured?",
        False,
    ),
}

_AUTOMATION_DEPENDENCIES: dict[AutomationPhase, set[str]] = {
    AutomationPhase.INFRA: {"Docker Engine", "Docker Compose v2"},
    AutomationPhase.SECRETS: {"Docker Engine", "Docker Compose v2"},
    AutomationPhase.STRIPE: {"Stripe CLI"},
}

_AUTOMATION_PROFILE_LIMITS: dict[AutomationPhase, set[str] | None] = {
    AutomationPhase.INFRA: {"local"},
    AutomationPhase.SECRETS: {"local"},
    AutomationPhase.STRIPE: None,
}


class SetupWizard:
    def __init__(
        self,
        *,
        ctx: CLIContext,
        profile: str,
        output_format: str,
        input_provider: InputProvider | None,
        summary_path: Path | None = None,
        markdown_summary_path: Path | None = None,
        automation_overrides: dict[AutomationPhase, bool | None] | None = None,
    ) -> None:
        backend_env, frontend_env, frontend_path = build_env_files(ctx)
        self.ctx = ctx
        self.output_format = output_format
        self.input_provider = input_provider
        self.automation_overrides = automation_overrides or {}
        self.context = WizardContext(
            cli_ctx=ctx,
            profile=profile,
            backend_env=backend_env,
            frontend_env=frontend_env,
            frontend_path=frontend_path,
            summary_path=summary_path,
            markdown_summary_path=markdown_summary_path,
        )

    # ------------------------------------------------------------------
    # Public entrypoints
    # ------------------------------------------------------------------
    def execute(self) -> None:
        provider = self._require_inputs()
        self.context.is_headless = hasattr(provider, "answers")
        console.info("Starting setup wizard …", topic="wizard")
        run_preflight(self.context)
        self._configure_automation(provider)

        infra_session = InfraSession(self.context)
        self.context.infra_session = infra_session
        try:
            infra_session.ensure_compose()

            core.run(self.context, provider)
            secrets.run(self.context, provider)
            security.run(self.context, provider)
            providers.run(self.context, provider)
            observability.run(self.context, provider)
            signup.run(self.context, provider)
            frontend.configure(self.context, provider)

            self.context.save_env_files()
            self.context.load_environment()
            self.context.refresh_settings_cache()
            capture_tenant_summary(self.context)

            sections = audit.build_sections(self.context)
            self._render(sections)
            audit.render_schema_summary(self.context)
            audit.write_summary(self.context, sections)
            audit.write_markdown_summary(self.context, sections)
        finally:
            infra_session.cleanup()

    def render_report(self) -> None:
        sections = audit.build_sections(self.context)
        self._render(sections)

    # ------------------------------------------------------------------
    # Helper utilities
    # ------------------------------------------------------------------
    @property
    def summary_path(self) -> Path | None:  # pragma: no cover - passthrough
        return self.context.summary_path

    @summary_path.setter
    def summary_path(self, value: Path | None) -> None:  # pragma: no cover - passthrough
        self.context.summary_path = value

    @property
    def markdown_summary_path(self) -> Path | None:  # pragma: no cover
        return self.context.markdown_summary_path

    @markdown_summary_path.setter
    def markdown_summary_path(self, value: Path | None) -> None:  # pragma: no cover
        self.context.markdown_summary_path = value

    def _render(self, sections: Sequence[SectionResult]) -> None:
        audit.render_sections(self.context, output_format=self.output_format, sections=sections)

    def _configure_automation(self, provider: InputProvider) -> None:
        console.info("Configuring automation preferences …", topic="wizard")
        for phase in ALL_AUTOMATION_PHASES:
            key, prompt, default = _AUTOMATION_PROMPTS[phase]
            override = self.automation_overrides.get(phase)
            if override is not None:
                enabled = override
                source = "CLI flag"
            else:
                enabled = provider.prompt_bool(key=key, prompt=prompt, default=default)
                source = "answers/prompt"
            blockers = self._missing_dependencies_for_phase(phase)
            blockers.extend(self._profile_blockers(phase))
            self.context.automation.request(
                phase,
                enabled=enabled,
                blocked_reasons=blockers if enabled else None,
            )
            if override is not None:
                state = "enabled" if enabled else "disabled"
                console.info(
                    f"{phase.value} automation {state} via {source}.",
                    topic="wizard",
                )
            if blockers and enabled:
                blocker_list = ", ".join(blockers)
                console.warn(
                    (
                        f"{phase.value.capitalize()} automation blocked due to "
                        f"missing dependencies: {blocker_list}."
                    ),
                    topic="wizard",
                )
            elif enabled:
                console.success(f"{phase.value.capitalize()} automation enabled.", topic="wizard")
            else:
                console.info(f"{phase.value.capitalize()} automation disabled.", topic="wizard")

    def _missing_dependencies_for_phase(self, phase: AutomationPhase) -> list[str]:
        required = _AUTOMATION_DEPENDENCIES.get(phase, set())
        if not required:
            return []
        status_lookup = {status.name: status for status in self.context.dependency_statuses}
        missing: list[str] = []
        for dependency in required:
            dep_status = status_lookup.get(dependency)
            if dep_status is None or dep_status.status != "ok":
                missing.append(dependency)
        return missing

    def _profile_blockers(self, phase: AutomationPhase) -> list[str]:
        allowed = _AUTOMATION_PROFILE_LIMITS.get(phase)
        if not allowed:
            return []
        if self.context.profile not in allowed:
            allowed_list = ", ".join(sorted(allowed))
            return [f"Supported only for {allowed_list} profile(s)."]
        return []

    def _require_inputs(self) -> InputProvider:
        if self.input_provider is None:
            raise CLIError(
                "This command requires inputs. Provide --answers-file/--var overrides or "
                "run without --non-interactive."
            )
        return self.input_provider


__all__ = ["SetupWizard", "PROFILE_CHOICES", "FRONTEND_ENV_RELATIVE"]
