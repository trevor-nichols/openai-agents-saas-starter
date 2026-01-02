"""Unit tests for core normalization helpers."""

from __future__ import annotations

import pytest

from app.core.normalization import normalize_email


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("", None),
        ("  ", None),
        ("User@Example.com", "user@example.com"),
        ("  User@Example.com  ", "user@example.com"),
    ],
)
def test_normalize_email(value: str | None, expected: str | None) -> None:
    assert normalize_email(value) == expected
