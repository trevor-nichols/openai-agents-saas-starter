"""Custom exceptions for Starter Console."""

from __future__ import annotations


class CLIError(RuntimeError):
    """Raised for operator-facing CLI failures."""


__all__ = ["CLIError"]
