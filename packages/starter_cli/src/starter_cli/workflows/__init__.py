"""Workflow packages for Starter CLI."""

from __future__ import annotations

import importlib
from typing import Any

_SUBMODULES = {
    "home": "starter_cli.workflows.home",
    "secrets": "starter_cli.workflows.secrets",
    "setup": "starter_cli.workflows.setup",
    "setup_menu": "starter_cli.workflows.setup_menu",
    "stripe": "starter_cli.workflows.stripe",
    "usage": "starter_cli.workflows.usage",
}


def __getattr__(name: str) -> Any:
    target = _SUBMODULES.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return importlib.import_module(target)


__all__ = sorted(_SUBMODULES.keys())
