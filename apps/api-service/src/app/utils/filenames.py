"""Filename and Content-Disposition helpers."""

from __future__ import annotations

import re

_CONTROL_CHARS = re.compile(r"[\r\n\t]+")


def sanitize_download_filename(value: str | None) -> str | None:
    """Return a header-safe filename or None if the value is empty."""

    name = (value or "").strip()
    if not name:
        return None
    # Drop any path components.
    name = name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    name = _CONTROL_CHARS.sub(" ", name).strip()
    # Avoid quotes/newlines in header value.
    name = name.replace('"', "'")
    name = name[:150].strip()
    return name or None


__all__ = ["sanitize_download_filename"]
