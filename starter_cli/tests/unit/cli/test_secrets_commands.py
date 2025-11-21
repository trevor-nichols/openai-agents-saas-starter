from __future__ import annotations

import builtins

import pytest
from starter_cli.commands.secrets import PROVIDER_OPTIONS, _resolve_provider_choice
from starter_cli.core import CLIError


def test_resolve_provider_choice_non_interactive_requires_arg() -> None:
    with pytest.raises(CLIError):
        _resolve_provider_choice(None, True)


def test_resolve_provider_choice_interactive(monkeypatch) -> None:
    # simulate selecting the second option
    monkeypatch.setattr(builtins, "input", lambda _: "2")

    option = _resolve_provider_choice(None, False)
    assert option is PROVIDER_OPTIONS[1]
