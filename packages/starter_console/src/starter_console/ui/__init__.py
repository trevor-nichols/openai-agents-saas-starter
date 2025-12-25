"""Textual hub for the Starter Console.

This package defines the interactive TUI shell, navigation, and screen
placeholders that host workflow-driven views. The hub is the default
entrypoint when no subcommand is provided.
"""

from .app import StarterTUI

__all__ = ["StarterTUI"]
