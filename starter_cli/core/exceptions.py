"""Custom exceptions for Starter CLI."""

from __future__ import annotations


class CLIError(RuntimeError):
    """Raised for operator-facing CLI failures."""


__all__ = ["CLIError"]
