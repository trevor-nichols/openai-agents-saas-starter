from __future__ import annotations

from starter_console.workflows.secrets import registry
from starter_contracts.secrets.models import SecretsProviderLiteral


def test_registry_covers_all_literals() -> None:
    options = registry.provider_options()
    literals = {option.literal for option in options}
    assert literals == set(SecretsProviderLiteral)
    for literal in literals:
        runner = registry.get_runner(literal)
        assert callable(runner)
        option = registry.get_option(literal)
        assert option.literal == literal
