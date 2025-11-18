from __future__ import annotations

import argparse

from starter_shared.secrets.models import SecretsProviderLiteral

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIContext, CLIError
from starter_cli.telemetry import append_verification_artifact

from starter_cli.workflows.secrets import registry
from starter_cli.workflows.secrets.models import (
    ProviderOption,
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


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    secrets_parser = subparsers.add_parser("secrets", help="Secrets provider workflows.")
    secrets_subparsers = secrets_parser.add_subparsers(dest="secrets_command")

    onboard_parser = secrets_subparsers.add_parser(
        "onboard",
        help="Guided setup for the secrets/signing provider.",
    )
    onboard_parser.add_argument(
        "--provider",
        choices=[choice.value for choice in SecretsProviderLiteral],
        help="Secrets provider to configure (defaults to interactive menu).",
    )
    onboard_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Disable prompts and rely entirely on --answers-file/--var.",
    )
    onboard_parser.add_argument(
        "--answers-file",
        action="append",
        default=[],
        help="JSON file containing KEY: value pairs for prompts (repeatable).",
    )
    onboard_parser.add_argument(
        "--var",
        action="append",
        default=[],
        help="Override a prompt answer, e.g. --var VAULT_ADDR=https://vault.local",
    )
    onboard_parser.add_argument(
        "--skip-make",
        action="store_true",
        help="Do not invoke make targets even if the workflow normally offers to do so.",
    )
    onboard_parser.set_defaults(handler=handle_onboard)


PROVIDER_OPTIONS: tuple[ProviderOption, ...] = registry.provider_options()


def handle_onboard(args: argparse.Namespace, ctx: CLIContext) -> int:
    option = _resolve_provider_choice(args.provider, args.non_interactive)
    if not option.available:
        console.warn(
            f"{option.label} is not yet available. "
            "Keep SECRETS_PROVIDER set to vault_dev until provider support lands.",
            topic="secrets",
        )
        return 1

    answers = _load_answers(args)
    input_provider: InputProvider
    if args.non_interactive:
        input_provider = HeadlessInputProvider(answers)
    else:
        input_provider = InteractiveInputProvider(answers)

    runner = registry.get_runner(option.literal)
    options = SecretsWorkflowOptions(skip_make=args.skip_make)
    result = runner(ctx, input_provider, options=options)
    render_onboard_result(result)
    emit_cli_telemetry(result.provider.value, success=True)
    if result.artifacts:
        log_path = ctx.project_root / "var/reports/verification-artifacts.json"
        for artifact in result.artifacts:
            append_verification_artifact(log_path, artifact)
        console.info(
            f"Logged {len(result.artifacts)} verification artifact(s) to {log_path}",
            topic="secrets",
        )
    return 0


def _resolve_provider_choice(
    provider_arg: str | None,
    non_interactive: bool,
) -> ProviderOption:
    if provider_arg:
        literal = SecretsProviderLiteral(provider_arg)
        return next(option for option in PROVIDER_OPTIONS if option.literal is literal)

    if non_interactive:
        raise CLIError("--provider is required when --non-interactive is set.")

    console.info("Select a secrets provider:", topic="secrets")
    for idx, option in enumerate(PROVIDER_OPTIONS, start=1):
        status = "" if option.available else " (coming soon)"
        console.info(f"{idx}. {option.label}{status}", topic="secrets")
        console.info(f"   {option.description}", topic="secrets")

    while True:
        choice = input("Enter provider number: ").strip()
        if not choice.isdigit():
            console.warn("Please enter a numeric choice.", topic="secrets")
            continue
        idx = int(choice)
        if 1 <= idx <= len(PROVIDER_OPTIONS):
            return PROVIDER_OPTIONS[idx - 1]
        console.warn("Choice out of range.", topic="secrets")


def _load_answers(args: argparse.Namespace) -> ParsedAnswers:
    answers = load_answers_files(args.answers_file or [])
    if args.var:
        answers = merge_answer_overrides(answers, args.var)
    return answers


__all__ = ["register"]
