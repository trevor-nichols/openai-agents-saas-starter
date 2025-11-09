"""Centralized password policy validation helpers."""

from __future__ import annotations

import re
from collections.abc import Iterable

from zxcvbn import zxcvbn

MIN_LENGTH = 14
MIN_REQUIRED_CATEGORIES = 2
MIN_ZXCVBN_SCORE = 3


class PasswordPolicyError(ValueError):
    """Raised when a password fails strength validation."""


_CATEGORY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"[A-Z]"),
    re.compile(r"[a-z]"),
    re.compile(r"[0-9]"),
    re.compile(r"[^A-Za-z0-9]"),
)


def _category_count(value: str) -> int:
    return sum(1 for pattern in _CATEGORY_PATTERNS if pattern.search(value))


def validate_password_strength(password: str, *, user_inputs: Iterable[str] | None = None) -> None:
    """Ensure the supplied password meets entropy and composition rules."""

    if len(password) < MIN_LENGTH:
        raise PasswordPolicyError(f"Password must be at least {MIN_LENGTH} characters long.")

    if _category_count(password) < MIN_REQUIRED_CATEGORIES:
        raise PasswordPolicyError(
            "Password must include at least two categories (upper, lower, digit, symbol)."
        )

    hints = [value for value in (user_inputs or ()) if value]
    analysis = zxcvbn(password, user_inputs=hints)
    score = analysis.get("score", 0)
    if score < MIN_ZXCVBN_SCORE:
        raise PasswordPolicyError("Password is too weak according to the current policy.")


__all__ = ["PasswordPolicyError", "validate_password_strength"]
