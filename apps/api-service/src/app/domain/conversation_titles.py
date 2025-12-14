"""Conversation title/display-name invariants.

Kept in the domain layer so both API validation and service orchestration can
share a single source of truth for normalization rules.
"""

from __future__ import annotations

import re

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_display_name(value: str, *, max_length: int = 128) -> str:
    """Normalize and validate a user-provided conversation title.

    Rules:
    - Trim leading/trailing whitespace
    - Collapse internal whitespace/newlines to single spaces
    - Enforce non-empty and length limit
    """

    normalized = (value or "").strip()
    # Normalize newlines and collapse any whitespace runs.
    normalized = normalized.replace("\r", " ").replace("\n", " ")
    normalized = _WHITESPACE_RE.sub(" ", normalized).strip()

    if not normalized:
        raise ValueError("display_name must not be empty")
    if len(normalized) > max_length:
        raise ValueError(f"display_name must be {max_length} characters or fewer")
    return normalized


__all__ = ["normalize_display_name"]

