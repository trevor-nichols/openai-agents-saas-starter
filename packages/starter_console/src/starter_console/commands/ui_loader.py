from __future__ import annotations

import importlib
import sys
from types import ModuleType

import starter_console


def load_ui_module() -> ModuleType:
    module = sys.modules.get("starter_console.ui")
    if module is None:
        candidate = getattr(starter_console, "ui", None)
        if isinstance(candidate, ModuleType):
            module = candidate
        else:
            module = importlib.import_module("starter_console.ui")
    return module


__all__ = ["load_ui_module"]
