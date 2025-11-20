"""Command registrations for the Starter CLI."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from importlib import import_module
from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:  # pragma: no cover - typing helper
    ParserSubparsers: TypeAlias = argparse._SubParsersAction[argparse.ArgumentParser]
else:  # pragma: no cover - runtime shim
    ParserSubparsers = argparse._SubParsersAction

_COMMAND_MODULES = (
    "starter_cli.commands.api",
    "starter_cli.commands.auth",
    "starter_cli.commands.config",
    "starter_cli.commands.infra",
    "starter_cli.commands.providers",
    "starter_cli.commands.release",
    "starter_cli.commands.secrets",
    "starter_cli.commands.status",
    "starter_cli.commands.stripe",
    "starter_cli.commands.setup",
    "starter_cli.commands.users",
    "starter_cli.commands.usage",
    "starter_cli.commands.util",
)


def register_all(subparsers: ParserSubparsers) -> None:
    for module_name in _COMMAND_MODULES:
        module = import_module(module_name)
        register: Callable[[ParserSubparsers], None] = module.register
        register(subparsers)


__all__ = ["register_all"]
