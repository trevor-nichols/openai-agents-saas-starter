from __future__ import annotations

import pytest

from starter_cli.core import CLIError
from starter_cli.ports.console import StdConsole
from ._stubs import StubInputProvider
from starter_cli.workflows.secrets import registry
from starter_cli.workflows.secrets.flow import select_provider
from starter_cli.workflows.secrets.models import ProviderOption


def test_select_provider_non_interactive_requires_arg() -> None:
    with pytest.raises(CLIError):
        select_provider(
            None,
            non_interactive=True,
            prompt=StubInputProvider(),
            console=StdConsole(),
        )


def test_select_provider_interactive() -> None:
    options: tuple[ProviderOption, ...] = registry.provider_options()
    target = options[1]
    prompt = StubInputProvider(strings={"SECRETS_PROVIDER": target.literal.value})

    option = select_provider(
        None,
        non_interactive=False,
        prompt=prompt,
        console=StdConsole(),
        options=options,
    )
    assert option is target
