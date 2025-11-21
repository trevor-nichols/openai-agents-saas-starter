"""Starter CLI package.

This module injects the backend source directory (``api-service``)
into ``sys.path`` so CLI commands can import FastAPI modules (``app.*``)
without manual ``PYTHONPATH`` edits.

Avoid importing ``starter_cli.app`` here to keep ``python -m starter_cli.app``
free of runpy warnings about preloaded modules. The app module remains
accessible via a lazy module attribute below.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parent
_BACKEND_ROOT = _PACKAGE_ROOT.parent / "api-service"

if _BACKEND_ROOT.exists():
    backend_path = str(_BACKEND_ROOT)
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)


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
