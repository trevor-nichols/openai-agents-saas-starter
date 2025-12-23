from __future__ import annotations

import re
import subprocess
import time
from dataclasses import dataclass

from starter_cli.core import CLIError

WHSEC_PATTERN = re.compile(r"whsec_[A-Za-z0-9]+")


@dataclass(slots=True)
class StripeCli:
    def version(self) -> str:
        try:
            result = subprocess.run(
                ["stripe", "--version"],
                check=True,
                text=True,
                capture_output=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            raise CLIError(
                "Stripe CLI not found. Install from https://docs.stripe.com/stripe-cli."
            ) from exc
        return result.stdout.strip()

    def is_authenticated(self) -> bool:
        try:
            subprocess.run(
                ["stripe", "config", "--list"],
                check=True,
                text=True,
                capture_output=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
        return True

    def login_interactive(self) -> None:
        subprocess.run(["stripe", "login", "--interactive"], check=True)

    def capture_webhook_secret(self, forward_url: str, *, timeout_sec: float = 15.0) -> str:
        listener_cmd = [
            "stripe",
            "listen",
            "--print-secret",
            "--forward-to",
            forward_url,
        ]
        try:
            process = subprocess.Popen(
                listener_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
        except FileNotFoundError as exc:  # pragma: no cover - runtime dependency
            raise CLIError(
                "Stripe CLI not found. Install from https://docs.stripe.com/stripe-cli."
            ) from exc

        secret: str | None = None
        last_line: str | None = None
        start = time.monotonic()
        try:
            if process.stdout is None:  # pragma: no cover - defensive
                raise CLIError("Unable to read output from Stripe CLI.")
            for line in process.stdout:
                last_line = line.rstrip()
                match = WHSEC_PATTERN.search(last_line)
                if match:
                    secret = match.group(0)
                    break
                if (time.monotonic() - start) > timeout_sec:
                    break
        finally:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:  # pragma: no cover - defensive
                process.kill()

        if not secret:
            detail = f" Last Stripe CLI output: {last_line}" if last_line else ""
            raise CLIError(
                "Stripe CLI did not emit a webhook signing secret. "
                "Ensure `stripe login` has completed and try again." + detail
            )
        return secret


__all__ = ["StripeCli"]
