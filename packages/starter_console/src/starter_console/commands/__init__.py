"""Command registrations for the Starter Console."""

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
    "starter_console.commands.api",
    "starter_console.commands.auth",
    "starter_console.commands.config",
    "starter_console.commands.doctor",
    "starter_console.commands.home",
    "starter_console.commands.infra",
    "starter_console.commands.logs",
    "starter_console.commands.providers",
    "starter_console.commands.release",
    "starter_console.commands.secrets",
    "starter_console.commands.sso",
    "starter_console.commands.start",
    "starter_console.commands.status",
    "starter_console.commands.stripe",
    "starter_console.commands.setup",
    "starter_console.commands.stop",
    "starter_console.commands.users",
    "starter_console.commands.usage",
    "starter_console.commands.util",
)


def register_all(subparsers: ParserSubparsers) -> None:
    for module_name in _COMMAND_MODULES:
        module = import_module(module_name)
        register: Callable[[ParserSubparsers], None] = module.register
        register(subparsers)


__all__ = ["register_all"]
