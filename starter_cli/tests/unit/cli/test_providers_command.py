from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from typing import cast

import pytest
from starter_cli.commands import providers as providers_commands
from starter_cli.core import CLIContext
from starter_contracts.config import StarterSettingsProtocol
from starter_contracts.provider_validation import ProviderViolation


@dataclass(slots=True)
class _DummySettings:
    enable_billing: bool = False
    _strict: bool = False

    def should_enforce_secret_overrides(self) -> bool:
        return self._strict


def _run_handler(
    monkeypatch: pytest.MonkeyPatch,
    *,
    settings: _DummySettings,
    violations: list[ProviderViolation],
) -> int:
    ctx = CLIContext()
    ctx.settings = cast(StarterSettingsProtocol, settings)
    args = argparse.Namespace(strict=False)

    def _mock_validate(current_settings, *, strict):
        assert current_settings is settings
        assert isinstance(strict, bool)
        return [replace(violation) for violation in violations]

    monkeypatch.setattr(providers_commands, "validate_providers", _mock_validate)

    return providers_commands.handle_validate_providers(args, ctx)


def test_providers_cli_fails_on_stripe_gaps(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _DummySettings(enable_billing=True)
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


def test_providers_cli_warns_when_non_stripe_and_not_strict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _DummySettings(enable_billing=False)
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
