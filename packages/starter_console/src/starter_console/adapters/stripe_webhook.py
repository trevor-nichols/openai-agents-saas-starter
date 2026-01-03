from __future__ import annotations

from starter_console.adapters.stripe_cli import StripeCli
from starter_console.ports.console import ConsolePort
from starter_console.ports.presentation import PromptPort
from starter_console.ports.stripe import StripeWebhookCapturePort
from starter_console.workflows.stripe.cli_helpers import ensure_stripe_cli


class StripeWebhookCaptureAdapter(StripeWebhookCapturePort):
    def __init__(
        self,
        *,
        console: ConsolePort,
        prompt: PromptPort,
        non_interactive: bool,
    ) -> None:
        self._console = console
        self._prompt = prompt
        self._non_interactive = non_interactive
        self._cli = StripeCli()

    def capture_webhook_secret(self, *, forward_url: str) -> str:
        ensure_stripe_cli(
            cli=self._cli,
            console=self._console,
            prompt=self._prompt,
            non_interactive=self._non_interactive,
        )
        return self._cli.capture_webhook_secret(forward_url)


__all__ = ["StripeWebhookCaptureAdapter"]
