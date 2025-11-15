from __future__ import annotations

import argparse
from pathlib import Path

from .common import CLIContext
from .console import console
from .setup import (
    HeadlessInputProvider,
    InteractiveInputProvider,
    SetupWizard,
    load_answers_files,
    merge_answer_overrides,
)
from .setup.wizard import PROFILE_CHOICES


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    setup_parser = subparsers.add_parser("setup", help="Bootstrap and policy wizard.")
    setup_subparsers = setup_parser.add_subparsers(dest="setup_command")

    wizard_parser = setup_subparsers.add_parser(
        "wizard",
        help="Guided checklist that aligns with CLI milestones (M1-M4).",
    )
    wizard_parser.add_argument(
        "--profile",
        choices=PROFILE_CHOICES,
        default="local",
        help="Target deployment profile. Influences required checks and defaults.",
    )
    wizard_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run without prompts (requires --answers-file/--var for required values).",
    )
    wizard_parser.add_argument(
        "--report-only",
        action="store_true",
        help="Skip prompts entirely and render the milestone audit report.",
    )
    wizard_parser.add_argument(
        "--output",
        choices={"summary", "json"},
        default="summary",
        help="Render a human-readable summary or machine-friendly JSON when auditing.",
    )
    wizard_parser.add_argument(
        "--answers-file",
        action="append",
        metavar="PATH",
        help="Path to a JSON file containing KEY: value answers for prompts (repeatable).",
    )
    wizard_parser.add_argument(
        "--var",
        action="append",
        metavar="KEY=VALUE",
        help="Override a specific prompt answer (repeatable).",
    )
    wizard_parser.add_argument(
        "--summary-path",
        metavar="PATH",
        help=(
            "Write a JSON summary of collected values + audit checks to PATH."
            " Defaults to var/reports/setup-summary.json when omitted."
        ),
    )
    wizard_parser.set_defaults(handler=handle_setup_wizard)


def handle_setup_wizard(args: argparse.Namespace, ctx: CLIContext) -> int:
    answers: dict[str, str] = {}
    if args.answers_file:
        answers = load_answers_files(args.answers_file)
    if args.var:
        answers = merge_answer_overrides(answers, args.var)

    provider = None
    if args.report_only:
        console.info("Report-only mode selected; skipping wizard prompts.", topic="wizard")
    elif args.non_interactive:
        provider = HeadlessInputProvider(answers=answers)
    else:
        provider = InteractiveInputProvider(prefill=dict(answers))

    wizard = SetupWizard(
        ctx=ctx,
        profile=args.profile,
        output_format=args.output,
        input_provider=provider,
    )
    if args.summary_path:
        wizard.summary_path = Path(args.summary_path).expanduser()

    if args.report_only:
        wizard.render_report()
    else:
        if not args.summary_path:
            default_summary = ctx.project_root / "var/reports/setup-summary.json"
            default_summary.parent.mkdir(parents=True, exist_ok=True)
            wizard.summary_path = default_summary
        wizard.execute()
    return 0


__all__ = ["register"]
