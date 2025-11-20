from __future__ import annotations

from collections.abc import Callable, Sequence
from functools import partial
from pathlib import Path

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIContext, CLIError

from ._wizard import audit
from ._wizard.context import FRONTEND_ENV_RELATIVE, WizardContext, build_env_files
from ._wizard.sections import (
    core,
    dev_user,
    frontend,
    integrations,
    observability,
    providers,
    secrets,
    security,
    signup,
    usage,
)
from .answer_recorder import AnswerRecorder, RecordingInputProvider
from .automation import ALL_AUTOMATION_PHASES, AutomationPhase
from .demo_token import run_demo_token_automation
from .dev_user import run_dev_user_automation
from .infra import InfraSession
from .inputs import InputProvider, InteractiveInputProvider, is_headless_provider
from .models import SectionResult
from .preflight import run_preflight
from .schema import load_schema
from .schema_provider import SchemaAwareInputProvider
from .section_specs import SECTION_LABELS, SECTION_SPECS
from .shell import WizardShell
from .state import WizardStateStore
from .tenant_summary import capture_tenant_summary
from .ui import WizardUIView
from .ui.commands import WizardUICommandHandler
from .ui.schema_metadata import build_section_prompt_metadata

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
    AutomationPhase.DEV_USER: (
        "AUTO_DEV_USER",
        "Seed a local dev user after setup completes?",
        True,
    ),
    AutomationPhase.DEMO_TOKEN: (
        "AUTO_DEMO_TOKEN",
        "Mint a demo service-account token for local testing?",
        True,
    ),
}

_AUTOMATION_DEPENDENCIES: dict[AutomationPhase, set[str]] = {
    AutomationPhase.INFRA: {"Docker Engine", "Docker Compose v2"},
    AutomationPhase.SECRETS: {"Docker Engine", "Docker Compose v2"},
    AutomationPhase.STRIPE: {"Stripe CLI"},
    AutomationPhase.MIGRATIONS: set(),
    AutomationPhase.REDIS: set(),
    AutomationPhase.GEOIP: set(),
    AutomationPhase.DEV_USER: set(),
    AutomationPhase.DEMO_TOKEN: set(),
}

_AUTOMATION_PROFILE_LIMITS: dict[AutomationPhase, set[str] | None] = {
    AutomationPhase.INFRA: {"local"},
    AutomationPhase.SECRETS: {"local"},
    AutomationPhase.STRIPE: None,
    AutomationPhase.MIGRATIONS: None,
    AutomationPhase.REDIS: None,
    AutomationPhase.GEOIP: None,
    AutomationPhase.DEV_USER: {"local"},
    AutomationPhase.DEMO_TOKEN: {"local"},
}

_AUTOMATION_LABELS: dict[AutomationPhase, str] = {
    AutomationPhase.INFRA: "Local Infra",
    AutomationPhase.SECRETS: "Vault Helpers",
    AutomationPhase.STRIPE: "Stripe Provisioning",
    AutomationPhase.MIGRATIONS: "DB Migrations",
    AutomationPhase.REDIS: "Redis Warm-up",
    AutomationPhase.GEOIP: "GeoIP Downloads",
    AutomationPhase.DEV_USER: "Dev User Seed",
    AutomationPhase.DEMO_TOKEN: "Demo Token",
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
        export_answers_path: Path | None = None,
        automation_overrides: dict[AutomationPhase, bool | None] | None = None,
        enable_tui: bool = True,
        enable_schema: bool = True,
        enable_shell: bool = True,
    ) -> None:
        backend_env, frontend_env, frontend_path = build_env_files(ctx)
        self.ctx = ctx
        self.output_format = output_format
        self.input_provider = input_provider
        self.automation_overrides = automation_overrides or {}
        self.enable_tui = enable_tui
        self.enable_shell = enable_shell
        self.schema = load_schema() if enable_schema else None
        self.state_store = WizardStateStore(ctx.project_root / "var/reports/wizard-state.json")
        self.export_answers_path = export_answers_path
        self._answer_recorder: AnswerRecorder | None = None
        section_prompt_metadata = build_section_prompt_metadata(self.schema)
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
            sections=[(spec.key, spec.label) for spec in SECTION_SPECS],
            automation=automation_labels,
            section_prompts=section_prompt_metadata,
            enabled=enable_tui,
        )
        self.context.ui = self.ui
        if isinstance(self.input_provider, InteractiveInputProvider) and self.ui.enabled:
            handler = WizardUICommandHandler(self.ui, SECTION_SPECS)
            self.input_provider.bind_ui_commands(handler)
        self.context.refresh_ui_prompts()
        self.section_states: dict[str, str] = {spec.key: "pending" for spec in SECTION_SPECS}

    # ------------------------------------------------------------------
    # Public entrypoints
    # ------------------------------------------------------------------
    def execute(self) -> None:
        provider = self._require_inputs()
        self.context.is_headless = is_headless_provider(provider)
        ui = self.ui if self._should_render_ui() else None
        if ui is not None:
            ui.start()
            ui.log("Starting setup wizard …")
        console.info("Starting setup wizard …", topic="wizard")
        infra_session: InfraSession | None = None
        try:
            run_preflight(self.context)
            self._configure_automation(provider)

            infra_session = InfraSession(self.context)
            self.context.infra_session = infra_session
            infra_session.ensure_compose()

            sections_completed = self._run_sections(provider)
            if not sections_completed:
                console.warn(
                    "Wizard exited before completing all sections; skipping finalization.",
                    topic="wizard",
                )
                return

            self._post_sections(provider)
            self._maybe_export_answers()
        except KeyboardInterrupt:
            console.warn("Setup wizard interrupted. Goodbye!", topic="wizard")
        finally:
            if infra_session is not None:
                infra_session.cleanup()
            if ui is not None:
                ui.stop()

    def render_report(self) -> None:
        sections = audit.build_sections(self.context)
        rendered = self._render(sections)
        if self.output_format == "checklist" and rendered:
            self._write_rendered_output(rendered)

    # ------------------------------------------------------------------
    # Section orchestration
    # ------------------------------------------------------------------
    def _run_sections(self, provider: InputProvider) -> bool:
        runners = self._build_section_runners(provider)
        if self._should_use_shell():
            shell = WizardShell(
                context=self.context,
                sections=SECTION_SPECS,
                section_states=self.section_states,
                runners=runners,
                run_section=lambda key, runner: self._run_section(
                    key,
                    runner,
                    fail_soft=True,
                ),
            )
            return shell.run()

        for spec in SECTION_SPECS:
            runner = runners[spec.key]
            self._run_section(spec.key, runner)
        return True

    def _post_sections(self, provider: InputProvider) -> None:
        self.context.save_env_files()
        self.context.load_environment()
        self.context.refresh_settings_cache()
        run_dev_user_automation(self.context)
        capture_tenant_summary(self.context)
        run_demo_token_automation(self.context)

        sections = audit.build_sections(self.context)
        self._render(sections)
        audit.render_schema_summary(self.context)
        audit.write_summary(self.context, sections)
        audit.write_markdown_summary(self.context, sections)
        self._finalize_run(provider)

    def _build_section_runners(self, provider: InputProvider) -> dict[str, Callable[[], None]]:
        return {
            "core": partial(core.run, self.context, provider),
            "secrets": partial(secrets.run, self.context, provider),
            "security": partial(security.run, self.context, provider),
            "providers": partial(providers.run, self.context, provider),
            "usage": partial(usage.run, self.context, provider),
            "observability": partial(observability.run, self.context, provider),
            "integrations": partial(integrations.run, self.context, provider),
            "signup": partial(signup.run, self.context, provider),
            "dev_user": partial(dev_user.run, self.context, provider),
            "frontend": partial(frontend.configure, self.context, provider),
        }

    def _should_use_shell(self) -> bool:
        return self.enable_shell and not self.context.is_headless

    def _should_render_ui(self) -> bool:
        return bool(self.ui and self.ui.enabled)

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

    def _render(self, sections: Sequence[SectionResult]) -> str | None:
        return audit.render_sections(
            self.context, output_format=self.output_format, sections=sections
        )

    def _write_rendered_output(self, text: str) -> None:
        path = self.context.markdown_summary_path
        if not path:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text.rstrip() + "\n", encoding="utf-8")
        console.success(f"Checklist written to {path}", topic="wizard")

    def _run_section(
        self,
        key: str,
        runner: Callable[[], None],
        *,
        fail_soft: bool = False,
    ) -> bool:
        label = SECTION_LABELS.get(key, key.title())
        self.section_states[key] = "running"
        if self.ui:
            self.ui.mark_section(key, "running", f"Collecting {label.lower()}.")
            self.ui.log(f"{label} in progress …")
        try:
            runner()
        except Exception:
            self.section_states[key] = "failed"
            if self.ui:
                self.ui.mark_section(
                    key,
                    "failed",
                    "Encountered an error.",
                )
                self.ui.log(f"{label} failed.")
            if fail_soft:
                return False
            raise
        else:
            self.section_states[key] = "done"
            if self.ui:
                self.ui.mark_section(key, "done", "Completed.")
                self.ui.log(f"{label} complete.")
            return True

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
        console.section("Next Actions", "Bring the stack online and smoke-test the flow.")
        console.step("1.", "Backend: run `hatch run serve`")
        console.step("2.", "Frontend: run `pnpm dev` inside web-app")
        if self.ui:
            self.ui.log("Ready for `hatch run serve` + `pnpm dev`.")

    def _configure_automation(self, provider: InputProvider) -> None:
        console.section(
            "Automation Preferences",
            "Decide which helper workflows (Docker, Vault, Stripe, etc.) should auto-run.",
        )
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
        provider: InputProvider = self.input_provider
        if self.export_answers_path:
            if not self._answer_recorder:
                self._answer_recorder = AnswerRecorder()
            if not isinstance(provider, RecordingInputProvider):
                provider = RecordingInputProvider(provider=provider, recorder=self._answer_recorder)
        if self.schema and not isinstance(provider, SchemaAwareInputProvider):
            if not self.state_store:
                raise CLIError("Wizard state store unavailable; cannot continue.")
            provider = SchemaAwareInputProvider(
                provider=provider,
                schema=self.schema,
                state=self.state_store,
                context=self.context,
            )
        self.input_provider = provider
        return provider

    def _maybe_export_answers(self) -> None:
        if not self.export_answers_path or not self._answer_recorder:
            return
        try:
            self._answer_recorder.export(self.export_answers_path)
        except OSError as exc:  # pragma: no cover - filesystem failures
            console.error(
                f"Failed to export answers to {self.export_answers_path}: {exc}",
                topic="wizard",
            )
            return
        console.success(
            f"Wrote prompt answers to {self.export_answers_path}",
            topic="wizard",
        )


__all__ = ["SetupWizard", "PROFILE_CHOICES", "FRONTEND_ENV_RELATIVE"]
