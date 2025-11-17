from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

from ..common import CLIContext, CLIError
from ..console import console
from ._wizard import audit
from ._wizard.context import FRONTEND_ENV_RELATIVE, WizardContext, build_env_files
from ._wizard.sections import (
    core,
    frontend,
    integrations,
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
from .schema import load_schema
from .schema_provider import SchemaAwareInputProvider
from .state import WizardStateStore
from .tenant_summary import capture_tenant_summary
from .ui import WizardUIView

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
    AutomationPhase.MIGRATIONS: (
        "AUTO_MIGRATIONS",
        "Automatically run database migrations after provider setup?",
        True,
    ),
    AutomationPhase.REDIS: (
        "AUTO_REDIS_WARMUP",
        "Validate Redis pools after configuration?",
        True,
    ),
    AutomationPhase.GEOIP: (
        "AUTO_GEOIP",
        "Automatically download GeoIP datasets when required?",
        False,
    ),
}

_AUTOMATION_DEPENDENCIES: dict[AutomationPhase, set[str]] = {
    AutomationPhase.INFRA: {"Docker Engine", "Docker Compose v2"},
    AutomationPhase.SECRETS: {"Docker Engine", "Docker Compose v2"},
    AutomationPhase.STRIPE: {"Stripe CLI"},
    AutomationPhase.MIGRATIONS: set(),
    AutomationPhase.REDIS: set(),
    AutomationPhase.GEOIP: set(),
}

_AUTOMATION_PROFILE_LIMITS: dict[AutomationPhase, set[str] | None] = {
    AutomationPhase.INFRA: {"local"},
    AutomationPhase.SECRETS: {"local"},
    AutomationPhase.STRIPE: None,
    AutomationPhase.MIGRATIONS: None,
    AutomationPhase.REDIS: None,
    AutomationPhase.GEOIP: None,
}

_SECTION_FLOW: list[tuple[str, str]] = [
    ("core", "Core & Metadata"),
    ("secrets", "Secrets & Vault"),
    ("security", "Security & Rate Limits"),
    ("providers", "Providers & Infra"),
    ("observability", "Tenant & Observability"),
    ("integrations", "Integrations"),
    ("signup", "Signup & Worker"),
    ("frontend", "Frontend"),
]

_AUTOMATION_LABELS: dict[AutomationPhase, str] = {
    AutomationPhase.INFRA: "Local Infra",
    AutomationPhase.SECRETS: "Vault Helpers",
    AutomationPhase.STRIPE: "Stripe Provisioning",
    AutomationPhase.MIGRATIONS: "DB Migrations",
    AutomationPhase.REDIS: "Redis Warm-up",
    AutomationPhase.GEOIP: "GeoIP Downloads",
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
        enable_tui: bool = True,
        enable_schema: bool = True,
    ) -> None:
        backend_env, frontend_env, frontend_path = build_env_files(ctx)
        self.ctx = ctx
        self.output_format = output_format
        self.input_provider = input_provider
        self.automation_overrides = automation_overrides or {}
        self.enable_tui = enable_tui
        self.schema = load_schema() if enable_schema else None
        self.state_store = WizardStateStore(ctx.project_root / "var/reports/wizard-state.json")
        self.context = WizardContext(
            cli_ctx=ctx,
            profile=profile,
            backend_env=backend_env,
            frontend_env=frontend_env,
            frontend_path=frontend_path,
            summary_path=summary_path,
            markdown_summary_path=markdown_summary_path,
            schema=self.schema,
            state_store=self.state_store,
        )
        automation_labels = [
            (phase.value, _AUTOMATION_LABELS[phase]) for phase in ALL_AUTOMATION_PHASES
        ]
        self.ui = WizardUIView(
            sections=_SECTION_FLOW,
            automation=automation_labels,
            enabled=enable_tui,
        )
        self.context.ui = self.ui

    # ------------------------------------------------------------------
    # Public entrypoints
    # ------------------------------------------------------------------
    def execute(self) -> None:
        provider = self._require_inputs()
        self.context.is_headless = hasattr(provider, "answers")
        self.ui.start()
        self.ui.log("Starting setup wizard …")
        console.info("Starting setup wizard …", topic="wizard")
        run_preflight(self.context)
        self._configure_automation(provider)

        infra_session = InfraSession(self.context)
        self.context.infra_session = infra_session
        try:
            infra_session.ensure_compose()

            self._run_section("core", lambda: core.run(self.context, provider))
            self._run_section("secrets", lambda: secrets.run(self.context, provider))
            self._run_section("security", lambda: security.run(self.context, provider))
            self._run_section("providers", lambda: providers.run(self.context, provider))
            self._run_section(
                "observability",
                lambda: observability.run(self.context, provider),
            )
            self._run_section("integrations", lambda: integrations.run(self.context, provider))
            self._run_section("signup", lambda: signup.run(self.context, provider))
            self._run_section("frontend", lambda: frontend.configure(self.context, provider))

            self.context.save_env_files()
            self.context.load_environment()
            self.context.refresh_settings_cache()
            capture_tenant_summary(self.context)

            sections = audit.build_sections(self.context)
            self._render(sections)
            audit.render_schema_summary(self.context)
            audit.write_summary(self.context, sections)
            audit.write_markdown_summary(self.context, sections)
            self._finalize_run(provider)
        finally:
            infra_session.cleanup()
            self.ui.stop()

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

    def _run_section(self, key: str, runner: Callable[[], None]) -> None:
        label = dict(_SECTION_FLOW).get(key, key.title())
        if self.ui:
            self.ui.mark_section(key, "running", f"Collecting {label.lower()}.")
            self.ui.log(f"{label} in progress …")
        try:
            runner()
        except Exception:
            if self.ui:
                self.ui.mark_section(
                    key,
                    "failed",
                    "Encountered an error.",
                )
                self.ui.log(f"{label} failed.")
            raise
        else:
            if self.ui:
                self.ui.mark_section(key, "done", "Completed.")
                self.ui.log(f"{label} complete.")

    def _finalize_run(self, provider: InputProvider) -> None:
        keep_compose = True
        if not self.context.is_headless:
            keep_compose = provider.prompt_bool(
                key="KEEP_INFRA_RUNNING",
                prompt="Keep the Docker compose stack running after the wizard?",
                default=True,
            )
        if keep_compose and self.context.infra_session:
            self.context.infra_session.keep_compose_active = True
            console.info("Docker compose will remain running for backend services.", topic="infra")
            if self.ui:
                self.ui.log("Docker compose left running.")
        else:
            console.info(
                "Docker compose will stop during cleanup (re-run `infra compose up` later).",
                topic="infra",
            )
        console.newline()
        console.info("Next actions", topic="wizard")
        console.info("1) Backend: run `hatch run serve`", topic="wizard")
        console.info(
            "2) Frontend: run `pnpm dev` inside agent-next-15-frontend",
            topic="wizard",
        )
        if self.ui:
            self.ui.log("Ready for `hatch run serve` + `pnpm dev`.")

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
            self._sync_automation_ui(phase)

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

    def _sync_automation_ui(self, phase: AutomationPhase) -> None:
        if not self.ui:
            return
        self.context.refresh_automation_ui(phase)

    def _require_inputs(self) -> InputProvider:
        if self.input_provider is None:
            raise CLIError(
                "This command requires inputs. Provide --answers-file/--var overrides or "
                "run without --non-interactive."
            )
        if not self.schema:
            return self.input_provider
        if not isinstance(self.input_provider, SchemaAwareInputProvider):
            if not self.state_store:
                raise CLIError("Wizard state store unavailable; cannot continue.")
            self.input_provider = SchemaAwareInputProvider(
                provider=self.input_provider,
                schema=self.schema,
                state=self.state_store,
                context=self.context,
            )
        return self.input_provider


__all__ = ["SetupWizard", "PROFILE_CHOICES", "FRONTEND_ENV_RELATIVE"]
