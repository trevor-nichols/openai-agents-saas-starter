from __future__ import annotations

import argparse

from starter_contracts.secrets.models import SecretsProviderLiteral

from starter_cli.core import CLIContext
from starter_cli.presenters.headless import build_headless_presenter
from starter_cli.workflows.secrets.flow import record_artifacts, run_onboard, select_provider
from starter_cli.workflows.secrets.models import (
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
        "--skip-automation",
        action="store_true",
        dest="skip_automation",
        help="Skip invoking local automation recipes (e.g., just dev-up) even if offered.",
    )
    onboard_parser.add_argument(
        "--skip-make",
        action="store_true",
        dest="skip_automation",
        help=argparse.SUPPRESS,
    )
    onboard_parser.set_defaults(handler=handle_onboard)


def handle_onboard(args: argparse.Namespace, ctx: CLIContext) -> int:
    console = ctx.console
    answers = _load_answers(args)
    input_provider: InputProvider
    if args.non_interactive:
        input_provider = HeadlessInputProvider(answers)
    else:
        presenter = ctx.presenter or build_headless_presenter(ctx.console)
        input_provider = InteractiveInputProvider(answers, presenter=presenter)

    option = select_provider(
        args.provider,
        non_interactive=args.non_interactive,
        prompt=input_provider,
        console=console,
    )
    if not option.available:
        console.warn(
            f"{option.label} is not yet available. "
            "Keep SECRETS_PROVIDER set to vault_dev until provider support lands.",
            topic="secrets",
        )
        return 1

    options = SecretsWorkflowOptions(skip_automation=args.skip_automation)
    result = run_onboard(ctx, provider=input_provider, option=option, options=options)
    render_onboard_result(console, result)
    emit_cli_telemetry(console, result.provider.value, success=True)
    log_path = ctx.project_root / "var/reports/verification-artifacts.json"
    record_artifacts(console, log_path=log_path, result=result)
    return 0


def _load_answers(args: argparse.Namespace) -> ParsedAnswers:
    answers = load_answers_files(args.answers_file or [])
    if args.var:
        answers = merge_answer_overrides(answers, args.var)
    return answers


__all__ = ["register"]
