"""StdConsole singleton used by CLI entrypoints and tests."""

from __future__ import annotations

from starter_console.ports.console import StdConsole

console = StdConsole()

__all__ = ["console"]
