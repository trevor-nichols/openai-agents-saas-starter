from __future__ import annotations

import argparse
from dataclasses import replace

from starter_cli.cli import providers_commands
from starter_cli.cli.common import CLIContext

from app.core.provider_validation import ProviderViolation


class DummyContext(CLIContext):
    def __init__(self, settings):
        super().__init__()
        self._settings = settings

    def require_settings(self):
        return self._settings


class DummySettings:
    def __init__(self, *, enable_billing: bool = False, strict: bool = False):
        self.enable_billing = enable_billing
        self._strict = strict

    def should_enforce_secret_overrides(self) -> bool:
        return self._strict


def _run_handler(monkeypatch, *, settings, violations):
    ctx = DummyContext(settings)
    args = argparse.Namespace(strict=False)

    def _mock_validate(current_settings, *, strict):
        assert current_settings is settings
        assert isinstance(strict, bool)
        return [replace(violation) for violation in violations]

    monkeypatch.setattr(providers_commands, "validate_providers", _mock_validate)

    return providers_commands.handle_validate_providers(args, ctx)


def test_providers_cli_fails_on_stripe_gaps(monkeypatch):
    settings = DummySettings(enable_billing=True)
    violations = [
        ProviderViolation(
            provider="stripe",
            code="missing_stripe_secret_key",
            message="missing",
            fatal=False,
        )
    ]

    exit_code = _run_handler(monkeypatch, settings=settings, violations=violations)

    assert exit_code == 1


def test_providers_cli_warns_when_non_stripe_and_not_strict(monkeypatch):
    settings = DummySettings(enable_billing=False)
    violations = [
        ProviderViolation(
            provider="resend",
            code="missing",
            message="missing",
            fatal=False,
        )
    ]

    exit_code = _run_handler(monkeypatch, settings=settings, violations=violations)

    assert exit_code == 0
