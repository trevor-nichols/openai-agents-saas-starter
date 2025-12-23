"""Starter CLI package."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starter_cli import adapters, app, workflows


def __getattr__(name: str):
    if name == "app":
        import importlib

        return importlib.import_module("starter_cli.app")
    if name == "adapters":
        import importlib

        return importlib.import_module("starter_cli.adapters")
    if name == "workflows":
        import importlib

        return importlib.import_module("starter_cli.workflows")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["app", "adapters", "workflows"]
