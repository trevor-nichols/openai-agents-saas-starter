from __future__ import annotations

import argparse
from pathlib import Path

from starter_console.core import CLIContext, CLIError
from starter_console.core.profiles import (
    load_frontend_env,
    load_profile_registry,
    select_profile,
    write_profile_manifest,
)
from starter_console.workflows.setup import (
    HeadlessInputProvider,
    SetupWizard,
    load_answers_files,
    merge_answer_overrides,
)
from starter_console.workflows.setup.automation import AutomationPhase
from starter_console.workflows.setup.inputs import InputProvider
from starter_console.workflows.setup_menu.controller import SetupMenuController


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    setup_parser = subparsers.add_parser("setup", help="Bootstrap and policy wizard.")
    setup_subparsers = setup_parser.add_subparsers(dest="setup_command")

    menu_parser = setup_subparsers.add_parser(
        "menu",
        help="Setup hub that shows status of workflows and quick-launches them.",
        aliases=["dashboard"],
    )
    menu_parser.add_argument(
        "--no-tui",
        action="store_true",
        help="Print a summary table instead of the interactive menu.",
    )
    menu_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit setup status as JSON (implies --no-tui).",
    )
    menu_parser.set_defaults(handler=handle_setup_menu)

    wizard_parser = setup_subparsers.add_parser(
        "wizard",
        help="Guided checklist that aligns with CLI milestones (M1-M4).",
    )
    wizard_parser.add_argument(
        "--profile",
        default=None,
        help="Target deployment profile. Defaults to auto-detect and config files.",
    )
    wizard_parser.add_argument(
        "--profiles-path",
        metavar="PATH",
        help="Optional profile config file path (defaults to config/starter-console.profile.yaml).",
    )
    wizard_parser.add_argument(
        "--strict",
        action="store_true",
        help="Production-only alias that enforces headless runs with pre-provided answers.",
    )
    wizard_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run without prompts (requires --answers-file/--var for required values).",
    )
    wizard_parser.add_argument(
        "--cli",
        action="store_true",
        help="Run the wizard in a curses-based CLI editor (no Textual UI).",
    )
    wizard_parser.add_argument(
        "--no-tui",
        action="store_true",
        help=(
            "Disable the Textual wizard UI (use with --non-interactive, --report-only, "
            "or --cli)."
        ),
    )
    wizard_parser.add_argument(
        "--report-only",
        action="store_true",
        help="Skip prompts entirely and render the milestone audit report.",
    )
    wizard_parser.add_argument(
        "--output",
        choices={"summary", "json", "checklist"},
        default="summary",
        help=(
            "Render a human-readable summary, machine-friendly JSON, or a Markdown checklist"
            " when auditing."
        ),
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
        "--export-answers",
        metavar="PATH",
        help="Write the collected prompt answers to PATH (JSON).",
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
        "--auto-sso",
        dest="auto_sso",
        action="store_const",
        const=True,
        default=None,
        help="Automatically seed SSO provider configuration after setup.",
    )
    wizard_parser.add_argument(
        "--no-auto-sso",
        dest="auto_sso",
        action="store_const",
        const=False,
        help="Disable SSO automation.",
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
    wizard_parser.add_argument(
        "--auto-dev-user",
        dest="auto_dev_user",
        action="store_const",
        const=True,
        default=None,
        help="Seed the demo dev user automatically after setup completes.",
    )
    wizard_parser.add_argument(
        "--no-auto-dev-user",
        dest="auto_dev_user",
        action="store_const",
        const=False,
        help="Disable dev-user seeding automation.",
    )
    wizard_parser.add_argument(
        "--auto-demo-token",
        dest="auto_demo_token",
        action="store_const",
        const=True,
        default=None,
        help="Mint a demo service-account token at the end of setup (demo profile).",
    )
    wizard_parser.add_argument(
        "--no-auto-demo-token",
        dest="auto_demo_token",
        action="store_const",
        const=False,
        help="Disable demo token automation.",
    )
    wizard_parser.set_defaults(handler=handle_setup_wizard)


def handle_setup_wizard(args: argparse.Namespace, ctx: CLIContext) -> int:
    registry = load_profile_registry(
        project_root=ctx.project_root,
        override_path=Path(args.profiles_path).expanduser()
        if args.profiles_path
        else None,
    )
    selection = select_profile(registry, explicit=args.profile)
    profile_id = selection.profile.profile_id
    if getattr(args, "strict", False):
        if profile_id != "production":
            raise CLIError("--strict is only supported with --profile production.")
        if not args.answers_file and not args.var:
            raise CLIError("--strict requires --answers-file or --var overrides.")
        args.non_interactive = True
    args.profile = profile_id
    frontend_env = load_frontend_env(project_root=ctx.project_root)
    write_profile_manifest(
        selection,
        project_root=ctx.project_root,
        frontend_env=frontend_env,
    )
    if args.export_answers and args.report_only:
        raise CLIError("--export-answers cannot be combined with --report-only.")
    if args.cli and args.non_interactive:
        raise CLIError("--cli cannot be combined with --non-interactive.")
    if args.cli and args.report_only:
        raise CLIError("--cli cannot be combined with --report-only.")

    answers: dict[str, str] = {}
    if args.answers_file:
        answers = load_answers_files(args.answers_file)
    if args.var:
        answers = merge_answer_overrides(answers, args.var)

    provider: InputProvider | None = None
    if args.report_only:
        ctx.console.info("Report-only mode selected; skipping wizard prompts.", topic="wizard")
    elif args.non_interactive:
        provider = HeadlessInputProvider(answers=answers)
    elif args.no_tui and not args.cli:
        raise CLIError(
            "--no-tui is only supported with --non-interactive, --report-only, or --cli."
        )

    automation_overrides = {
        phase: value
        for phase, value in {
            AutomationPhase.INFRA: args.auto_infra,
            AutomationPhase.SECRETS: args.auto_secrets,
            AutomationPhase.STRIPE: args.auto_stripe,
            AutomationPhase.SSO: args.auto_sso,
            AutomationPhase.MIGRATIONS: args.auto_migrations,
            AutomationPhase.REDIS: args.auto_redis,
            AutomationPhase.GEOIP: args.auto_geoip,
            AutomationPhase.DEV_USER: args.auto_dev_user,
            AutomationPhase.DEMO_TOKEN: args.auto_demo_token,
        }.items()
        if value is not None
    }

    interactive_run = not args.non_interactive and not args.report_only
    if interactive_run:
        if args.cli:
            from starter_console.ui.panes.wizard.paths import ensure_summary_paths
            from starter_console.workflows.setup.editor import run_editor

            summary_path, markdown_path = ensure_summary_paths(
                ctx,
                Path(args.summary_path).expanduser() if args.summary_path else None,
                Path(args.markdown_summary_path).expanduser()
                if args.markdown_summary_path
                else None,
            )
            run_editor(
                ctx,
                profile_id=args.profile,
                profiles_path=Path(args.profiles_path).expanduser()
                if args.profiles_path
                else None,
                answers=dict(answers),
                output_format=args.output,
                summary_path=summary_path,
                markdown_summary_path=markdown_path,
                export_answers_path=Path(args.export_answers).expanduser()
                if args.export_answers
                else None,
            )
            return 0

        from starter_console.ui.panes.wizard import WizardLaunchConfig

        from .ui_loader import load_ui_module

        wizard_config = WizardLaunchConfig(
            profile=args.profile,
            output_format=args.output,
            answers=dict(answers),
            summary_path=Path(args.summary_path).expanduser() if args.summary_path else None,
            markdown_summary_path=Path(args.markdown_summary_path).expanduser()
            if args.markdown_summary_path
            else None,
            export_answers_path=Path(args.export_answers).expanduser()
            if args.export_answers
            else None,
            automation_overrides=automation_overrides,
            profiles_path=Path(args.profiles_path).expanduser()
            if args.profiles_path
            else None,
            auto_start=True,
        )
        load_ui_module().StarterTUI(
            ctx, initial_screen="wizard", wizard_config=wizard_config
        ).run()
        return 0

    wizard = SetupWizard(
        ctx=ctx,
        profile=args.profile,
        profile_policy=selection.profile,
        output_format=args.output,
        input_provider=provider,
        export_answers_path=Path(args.export_answers).expanduser() if args.export_answers else None,
        markdown_summary_path=Path(args.markdown_summary_path).expanduser()
        if args.markdown_summary_path
        else None,
        automation_overrides=automation_overrides,
        enable_tui=False,
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


def handle_setup_menu(args: argparse.Namespace, ctx: CLIContext) -> int:
    controller = SetupMenuController(ctx)
    use_tui = not args.no_tui and not args.json
    if use_tui:
        from .ui_loader import load_ui_module

        load_ui_module().StarterTUI(ctx, initial_screen="setup").run()
        return 0
    return controller.run(output_json=args.json)


__all__ = ["register"]
