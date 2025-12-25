from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from starter_cli.core import CLIContext, CLIError
from starter_cli.presenters.headless import build_headless_presenter
from starter_cli.workflows.secrets.flow import record_artifacts, run_onboard, select_provider
from starter_cli.workflows.secrets.models import (
    OnboardResult,
    SecretsWorkflowOptions,
    emit_cli_telemetry,
    render_onboard_result,
)
from starter_cli.workflows.setup.inputs import (
    HeadlessInputProvider,
    InputProvider,
    InteractiveInputProvider,
    ParsedAnswers,
    load_answers_files,
    merge_answer_overrides,
)


@dataclass(frozen=True, slots=True)
class SecretsOnboardConfig:
    provider: str | None
    non_interactive: bool
    answers_files: Sequence[str] = ()
    overrides: Sequence[str] = ()
    skip_automation: bool = False


def run_secrets_onboard(ctx: CLIContext, config: SecretsOnboardConfig) -> OnboardResult:
    answers = _load_answers(config)
    input_provider = _build_input_provider(ctx, config, answers)
    return execute_secrets_onboard(
        ctx,
        provider=config.provider,
        non_interactive=config.non_interactive,
        input_provider=input_provider,
        skip_automation=config.skip_automation,
    )


def execute_secrets_onboard(
    ctx: CLIContext,
    *,
    provider: str | None,
    non_interactive: bool,
    input_provider: InputProvider,
    skip_automation: bool,
) -> OnboardResult:
    console = ctx.console
    option = select_provider(
        provider,
        non_interactive=non_interactive,
        prompt=input_provider,
        console=console,
    )
    if not option.available:
        console.warn(
            f"{option.label} is not yet available. "
            "Keep SECRETS_PROVIDER set to vault_dev until provider support lands.",
            topic="secrets",
        )
        raise CLIError("Selected secrets provider is not available yet.")

    options = SecretsWorkflowOptions(skip_automation=skip_automation)
    result = run_onboard(ctx, provider=input_provider, option=option, options=options)
    render_onboard_result(console, result)
    emit_cli_telemetry(console, result.provider.value, success=True)
    log_path = ctx.project_root / "var/reports/verification-artifacts.json"
    record_artifacts(console, log_path=log_path, result=result)
    return result


def _load_answers(config: SecretsOnboardConfig) -> ParsedAnswers:
    answers = load_answers_files(config.answers_files)
    if config.overrides:
        answers = merge_answer_overrides(answers, config.overrides)
    return answers


def _build_input_provider(
    ctx: CLIContext,
    config: SecretsOnboardConfig,
    answers: ParsedAnswers,
) -> InputProvider:
    if config.non_interactive:
        return HeadlessInputProvider(answers)
    presenter = ctx.presenter or build_headless_presenter(ctx.console)
    return InteractiveInputProvider(answers, presenter=presenter)


__all__ = [
    "SecretsOnboardConfig",
    "execute_secrets_onboard",
    "run_secrets_onboard",
]
