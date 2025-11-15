from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from ..common import CLIContext, CLIError
from ..console import console
from ._wizard import audit
from ._wizard.context import FRONTEND_ENV_RELATIVE, WizardContext, build_env_files
from ._wizard.sections import core, frontend, observability, providers, secrets, signup
from .inputs import InputProvider
from .models import SectionResult

PROFILE_CHOICES = ("local", "staging", "production")


class SetupWizard:
    def __init__(
        self,
        *,
        ctx: CLIContext,
        profile: str,
        output_format: str,
        input_provider: InputProvider | None,
        summary_path: Path | None = None,
    ) -> None:
        backend_env, frontend_env, frontend_path = build_env_files(ctx)
        self.ctx = ctx
        self.output_format = output_format
        self.input_provider = input_provider
        self.context = WizardContext(
            cli_ctx=ctx,
            profile=profile,
            backend_env=backend_env,
            frontend_env=frontend_env,
            frontend_path=frontend_path,
            summary_path=summary_path,
        )

    # ------------------------------------------------------------------
    # Public entrypoints
    # ------------------------------------------------------------------
    def execute(self) -> None:
        provider = self._require_inputs()
        self.context.is_headless = hasattr(provider, "answers")
        console.info("Starting setup wizard …", topic="wizard")

        core.run(self.context, provider)
        secrets.run(self.context, provider)
        providers.run(self.context, provider)
        observability.run(self.context, provider)
        signup.run(self.context, provider)
        frontend.configure(self.context, provider)

        self.context.save_env_files()
        self.context.load_environment()
        self.context.refresh_settings_cache()

        sections = audit.build_sections(self.context)
        self._render(sections)
        audit.render_schema_summary(self.context)
        audit.write_summary(self.context, sections)

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

    def _render(self, sections: Sequence[SectionResult]) -> None:
        audit.render_sections(self.context, output_format=self.output_format, sections=sections)

    def _require_inputs(self) -> InputProvider:
        if self.input_provider is None:
            raise CLIError(
                "This command requires inputs. Provide --answers-file/--var overrides or "
                "run without --non-interactive."
            )
        return self.input_provider


__all__ = ["SetupWizard", "PROFILE_CHOICES", "FRONTEND_ENV_RELATIVE"]
