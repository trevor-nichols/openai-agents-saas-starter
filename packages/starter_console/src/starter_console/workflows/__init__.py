"""Workflow packages for Starter Console."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from . import home, secrets, setup, setup_menu, stripe, usage

_SUBMODULES = {
    "home": "starter_console.workflows.home",
    "secrets": "starter_console.workflows.secrets",
    "setup": "starter_console.workflows.setup",
    "setup_menu": "starter_console.workflows.setup_menu",
    "stripe": "starter_console.workflows.stripe",
    "usage": "starter_console.workflows.usage",
}


def __getattr__(name: str) -> Any:
    target = _SUBMODULES.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return importlib.import_module(target)


__all__ = [
    "home",
    "secrets",
    "setup",
    "setup_menu",
    "stripe",
    "usage",
]
