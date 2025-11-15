from __future__ import annotations

import builtins

import pytest
from starter_cli.cli.common import CLIError
from starter_cli.cli.secrets_commands import PROVIDER_OPTIONS, _resolve_provider_choice


def test_resolve_provider_choice_non_interactive_requires_arg() -> None:
    with pytest.raises(CLIError):
        _resolve_provider_choice(None, True)


def test_resolve_provider_choice_interactive(monkeypatch) -> None:
    # simulate selecting the second option
    monkeypatch.setattr(builtins, "input", lambda _: "2")

    option = _resolve_provider_choice(None, False)
    assert option is PROVIDER_OPTIONS[1]
