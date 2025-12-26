from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from starter_contracts.secrets.models import SecretsProviderLiteral

from starter_console.core import CLIContext, CLIError
from starter_console.ports.console import ConsolePort
from starter_console.workflows.setup.inputs import InputProvider

from . import registry
from .models import OnboardResult, ProviderOption, SecretsWorkflowOptions


def select_provider(
    provider_arg: str | None,
    *,
    non_interactive: bool,
    prompt: InputProvider,
    console: ConsolePort,
    options: Sequence[ProviderOption] | None = None,
) -> ProviderOption:
    available = list(options or registry.provider_options())
    if not available:
        raise CLIError("No secrets providers are registered.")

    if provider_arg:
        literal = SecretsProviderLiteral(provider_arg)
        return next(option for option in available if option.literal is literal)

    if non_interactive:
        raise CLIError("--provider is required when --non-interactive is set.")

    console.info("Select a secrets provider:", topic="secrets")
    for option in available:
        status = "" if option.available else " (coming soon)"
        console.info(f"- {option.literal.value}: {option.label}{status}", topic="secrets")
        console.info(f"  {option.description}", topic="secrets")

    choices = [option.literal.value for option in available]
    selection = prompt.prompt_choice(
        key="SECRETS_PROVIDER",
        prompt="Secrets provider",
        choices=choices,
        default=choices[0] if choices else None,
    )
    return next(option for option in available if option.literal.value == selection)


def run_onboard(
    ctx: CLIContext,
    *,
    provider: InputProvider,
    option: ProviderOption,
    options: SecretsWorkflowOptions,
) -> OnboardResult:
    runner = registry.get_runner(option.literal)
    return runner(ctx, provider, options=options)


def record_artifacts(console: ConsolePort, *, log_path: Path, result: OnboardResult) -> None:
    if not result.artifacts:
        return
    from starter_console.telemetry import append_verification_artifact

    for artifact in result.artifacts:
        append_verification_artifact(log_path, artifact)
    console.info(
        f"Logged {len(result.artifacts)} verification artifact(s) to {log_path}",
        topic="secrets",
    )


__all__ = ["record_artifacts", "run_onboard", "select_provider"]
