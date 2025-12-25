from __future__ import annotations

import os
import subprocess
import sys

from starter_console.adapters.stripe_cli import StripeCli
from starter_console.core import CLIError
from starter_console.ports.console import ConsolePort
from starter_console.ports.presentation import PromptPort


def ensure_stripe_cli(
    *,
    cli: StripeCli,
    console: ConsolePort,
    prompt: PromptPort,
    non_interactive: bool,
) -> None:
    console.info("Checking Stripe CLI installation...", topic="stripe")
    version = cli.version()
    console.success(version, topic="stripe")

    if cli.is_authenticated():
        console.success("Stripe CLI authentication verified.", topic="stripe")
        return

    console.warn("Stripe CLI is not authenticated.", topic="stripe")
    if non_interactive:
        raise CLIError("Cannot continue without Stripe CLI authentication.")

    if prompt.prompt_bool(
        key="stripe_cli_auth_page",
        prompt="Open the Stripe CLI auth page?",
        default=False,
    ):
        _open_url(console, "https://dashboard.stripe.com/stripe-cli/auth")

    if prompt.prompt_bool(
        key="stripe_cli_login",
        prompt="Run `stripe login --interactive` now?",
        default=True,
    ):
        cli.login_interactive()
        if cli.is_authenticated():
            console.success("Stripe CLI authentication confirmed.", topic="stripe")
            return

    raise CLIError("Cannot continue without Stripe CLI authentication.")


def _open_url(console: ConsolePort, url: str) -> None:
    if sys.platform.startswith("darwin"):
        opener = "open"
    elif os.name == "nt":
        opener = "start"
    else:
        opener = "xdg-open"
    try:
        subprocess.Popen([opener, url])
        console.info(f"Opened {url} in your browser.")
    except OSError:
        console.warn(f"Unable to open {url}. Please visit it manually.")


__all__ = ["ensure_stripe_cli"]
