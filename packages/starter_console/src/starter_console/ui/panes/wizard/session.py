from __future__ import annotations

import threading

from starter_console.core import CLIContext
from starter_console.core.profiles import (
    load_frontend_env,
    load_profile_registry,
    select_profile,
    write_profile_manifest,
)
from starter_console.presenters import PresenterConsoleAdapter, build_textual_presenter
from starter_console.ui.context import derive_presenter_context
from starter_console.ui.prompting import PromptChannel, TextualPromptPort
from starter_console.workflows.setup import SetupWizard
from starter_console.workflows.setup.schema import load_schema
from starter_console.workflows.setup.section_specs import SECTION_SPECS
from starter_console.workflows.setup.ui import WizardUIView
from starter_console.workflows.setup.ui.schema_metadata import build_section_prompt_metadata
from starter_console.workflows.setup.wizard import build_automation_labels

from .models import WizardLaunchConfig
from .notify import WizardNotifyPort
from .paths import ensure_summary_paths


class WizardSession:
    def __init__(self, ctx: CLIContext, config: WizardLaunchConfig) -> None:
        self._ctx = ctx
        self._config = config
        self._prompt_channel = PromptChannel()
        self._thread: threading.Thread | None = None
        self._done = threading.Event()
        self.error: Exception | None = None
        self.state = self._build_state()

    @property
    def prompt_channel(self) -> PromptChannel:
        return self._prompt_channel

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def done(self) -> bool:
        return self._done.is_set()

    def start(self) -> None:
        if self.running:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _build_state(self) -> WizardUIView:
        schema = load_schema()
        section_prompts = build_section_prompt_metadata(schema)
        return WizardUIView(
            sections=[(spec.key, spec.label) for spec in SECTION_SPECS],
            automation=build_automation_labels(),
            section_prompts=section_prompts,
            enabled=True,
        )

    def _run(self) -> None:
        try:
            notify = WizardNotifyPort(self.state)
            prompt = TextualPromptPort(prefill=self._config.answers, channel=self._prompt_channel)
            presenter = build_textual_presenter(prompt=prompt, notify=notify)
            wizard_console = PresenterConsoleAdapter(presenter)
            wizard_ctx = derive_presenter_context(
                self._ctx, console=wizard_console, presenter=presenter
            )
            input_provider = prompt
            summary_path, markdown_path = ensure_summary_paths(
                self._ctx,
                self._config.summary_path,
                self._config.markdown_summary_path,
            )
            registry = load_profile_registry(
                project_root=self._ctx.project_root,
                override_path=self._config.profiles_path,
            )
            selection = select_profile(registry, explicit=self._config.profile)
            frontend_env = load_frontend_env(project_root=self._ctx.project_root)
            write_profile_manifest(
                selection,
                project_root=self._ctx.project_root,
                frontend_env=frontend_env,
            )
            wizard = SetupWizard(
                ctx=wizard_ctx,
                profile=selection.profile.profile_id,
                profile_policy=selection.profile,
                output_format=self._config.output_format,
                input_provider=input_provider,
                summary_path=summary_path,
                markdown_summary_path=markdown_path,
                export_answers_path=self._config.export_answers_path,
                automation_overrides=self._config.automation_overrides,
                enable_tui=True,
                wizard_ui=self.state,
            )
            wizard.execute()
        except Exception as exc:  # pragma: no cover - defensive
            self.error = exc
            self.state.log(f"Wizard failed: {exc}")
        finally:
            self._done.set()


__all__ = ["WizardSession"]
