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
from .setup.automation import AutomationPhase
from .setup.inputs import InputProvider
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
        "--no-tui",
        action="store_true",
        help="Disable the Rich status dashboard (use plain console output).",
    )
    wizard_parser.add_argument(
        "--legacy-flow",
        action="store_true",
        help="Use the legacy sequential prompts instead of the interactive shell dashboard.",
    )
    wizard_parser.add_argument(
        "--no-schema",
        action="store_true",
        help="Bypass the dependency graph (legacy prompt flow).",
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
    wizard_parser.add_argument(
        "--markdown-summary-path",
        metavar="PATH",
        help=(
            "Write a Markdown one-stop recap to PATH. Defaults to "
            "var/reports/cli-one-stop-summary.md."
        ),
    )
    wizard_parser.add_argument(
        "--auto-infra",
        dest="auto_infra",
        action="store_const",
        const=True,
        default=None,
        help="Automatically run Docker compose + Vault helpers during setup (overrides prompts).",
    )
    wizard_parser.add_argument(
        "--no-auto-infra",
        dest="auto_infra",
        action="store_const",
        const=False,
        help="Explicitly disable infra automation.",
    )
    wizard_parser.add_argument(
        "--auto-secrets",
        dest="auto_secrets",
        action="store_const",
        const=True,
        default=None,
        help=(
            "Automatically manage the Vault dev signer (start/stop) when "
            "Vault verification is enabled."
        ),
    )
    wizard_parser.add_argument(
        "--no-auto-secrets",
        dest="auto_secrets",
        action="store_const",
        const=False,
        help="Explicitly disable secrets automation.",
    )
    wizard_parser.add_argument(
        "--auto-stripe",
        dest="auto_stripe",
        action="store_const",
        const=True,
        default=None,
        help="Automatically run Stripe provisioning after providers are configured.",
    )
    wizard_parser.add_argument(
        "--no-auto-stripe",
        dest="auto_stripe",
        action="store_const",
        const=False,
        help="Explicitly disable Stripe automation.",
    )
    wizard_parser.add_argument(
        "--auto-migrations",
        dest="auto_migrations",
        action="store_const",
        const=True,
        default=None,
        help="Automatically run database migrations after providers complete.",
    )
    wizard_parser.add_argument(
        "--no-auto-migrations",
        dest="auto_migrations",
        action="store_const",
        const=False,
        help="Disable automatic migrations (wizard will prompt instead).",
    )
    wizard_parser.add_argument(
        "--auto-redis",
        dest="auto_redis",
        action="store_const",
        const=True,
        default=None,
        help="Automatically warm up Redis pools after configuration.",
    )
    wizard_parser.add_argument(
        "--no-auto-redis",
        dest="auto_redis",
        action="store_const",
        const=False,
        help="Skip Redis warm-up automation.",
    )
    wizard_parser.add_argument(
        "--auto-geoip",
        dest="auto_geoip",
        action="store_const",
        const=True,
        default=None,
        help="Download GeoIP datasets automatically when required.",
    )
    wizard_parser.add_argument(
        "--no-auto-geoip",
        dest="auto_geoip",
        action="store_const",
        const=False,
        help="Skip GeoIP download automation.",
    )
    wizard_parser.set_defaults(handler=handle_setup_wizard)


def handle_setup_wizard(args: argparse.Namespace, ctx: CLIContext) -> int:
    answers: dict[str, str] = {}
    if args.answers_file:
        answers = load_answers_files(args.answers_file)
    if args.var:
        answers = merge_answer_overrides(answers, args.var)

    provider: InputProvider | None = None
    if args.report_only:
        console.info("Report-only mode selected; skipping wizard prompts.", topic="wizard")
    elif args.non_interactive:
        provider = HeadlessInputProvider(answers=answers)
    else:
        provider = InteractiveInputProvider(prefill=dict(answers))

    automation_overrides = {
        phase: value
        for phase, value in {
            AutomationPhase.INFRA: args.auto_infra,
            AutomationPhase.SECRETS: args.auto_secrets,
            AutomationPhase.STRIPE: args.auto_stripe,
            AutomationPhase.MIGRATIONS: args.auto_migrations,
            AutomationPhase.REDIS: args.auto_redis,
            AutomationPhase.GEOIP: args.auto_geoip,
        }.items()
        if value is not None
    }

    shell_enabled = (
        not args.non_interactive
        and not args.report_only
        and not args.legacy_flow
        and not args.no_tui
    )

    wizard = SetupWizard(
        ctx=ctx,
        profile=args.profile,
        output_format=args.output,
        input_provider=provider,
        markdown_summary_path=Path(args.markdown_summary_path).expanduser()
        if args.markdown_summary_path
        else None,
        automation_overrides=automation_overrides,
        enable_tui=(not shell_enabled) and not args.no_tui,
        enable_schema=not args.no_schema,
        enable_shell=shell_enabled,
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
        if wizard.markdown_summary_path is None:
            default_md = ctx.project_root / "var/reports/cli-one-stop-summary.md"
            default_md.parent.mkdir(parents=True, exist_ok=True)
            wizard.markdown_summary_path = default_md
        wizard.execute()
    return 0


__all__ = ["register"]
