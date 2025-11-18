"""Starter CLI package.

This module also injects the backend source directory (``anything-agents``)
into ``sys.path`` so that CLI commands can reuse the FastAPI project's
modules (``app.*``) without requiring callers to set ``PYTHONPATH`` manually.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parent
_BACKEND_ROOT = _PACKAGE_ROOT.parent / "anything-agents"

if _BACKEND_ROOT.exists():
    backend_path = str(_BACKEND_ROOT)
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)

from . import app as app  # noqa: E402

__all__ = ["app"]
