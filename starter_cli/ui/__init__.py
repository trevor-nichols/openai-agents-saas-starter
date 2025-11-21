"""Textual-based TUI for the starter CLI.

This package hosts the shared app shell and page definitions used by
both the `home` command and the setup hub. Screens are registered
through the router in :mod:`starter_cli.ui.app` and consume the
existing workflow/domain logic instead of spawning subprocesses.
"""

from .app import StarterTUI

__all__ = ["StarterTUI"]
