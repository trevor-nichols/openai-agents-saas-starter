from __future__ import annotations

import argparse
from dataclasses import replace

from starter_contracts.provider_validation import validate_providers

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIContext

_DOC_PATH = "docs/ops/provider-parity.md"


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    providers_parser = subparsers.add_parser(
        "providers",
        help="Third-party provider helpers.",
    )
    providers_subparsers = providers_parser.add_subparsers(dest="providers_command")

    validate_parser = providers_subparsers.add_parser(
        "validate",
        help="Validate Stripe/Resend/Tavily configuration.",
    )
    validate_parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat every violation as fatal (useful for CI).",
    )
    validate_parser.set_defaults(handler=handle_validate_providers)


def handle_validate_providers(args: argparse.Namespace, ctx: CLIContext) -> int:
    settings = ctx.require_settings()
    strict = bool(args.strict) or settings.should_enforce_secret_overrides()

    violations = validate_providers(settings, strict=strict)

    if settings.enable_billing:
        violations = [
            replace(violation, fatal=True)
            if violation.provider == "stripe"
            else violation
            for violation in violations
        ]
    if not violations:
        console.success("All providers are configured.", topic="providers")
        return 0

    fatal = False
    for violation in violations:
        if violation.fatal:
            fatal = True
            console.error(violation.as_log_message(), topic="providers")
        else:
            console.warn(violation.as_log_message(), topic="providers")

    if fatal:
        console.error(
            f"Provider validation failed. See {_DOC_PATH} for remediation steps.",
            topic="providers",
        )
        return 1

    console.warn(
        "Provider validation finished with warnings only (local/dev mode).",
        topic="providers",
    )
    return 0


__all__ = ["register"]
