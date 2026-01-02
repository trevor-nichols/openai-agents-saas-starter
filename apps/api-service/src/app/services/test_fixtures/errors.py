"""Errors for deterministic test fixture seeding."""

from __future__ import annotations


class TestFixtureError(RuntimeError):
    """Raised when deterministic seed application fails."""


__all__ = ["TestFixtureError"]
