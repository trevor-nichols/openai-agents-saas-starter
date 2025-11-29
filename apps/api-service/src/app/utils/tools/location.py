"""Helpers for building safe user_location payloads for WebSearchTool."""

from __future__ import annotations

from typing import cast

from openai.types.responses.web_search_tool_param import UserLocation

from app.api.v1.chat.schemas import LocationHint


def build_web_search_location(
    location: LocationHint | None,
    *,
    share_location: bool,
) -> UserLocation | None:
    """Return a sanitized location payload for WebSearchTool or None.

    Only returns data when the caller explicitly opted in via `share_location`
    and at least one coarse field (city/region/country/timezone) is present.
    """

    if not share_location or location is None:
        return None

    fields: dict[str, str | None] = {
        "city": _clean(location.city),
        "region": _clean(location.region),
        "country": _clean(location.country),
        "timezone": _clean(location.timezone),
    }

    filtered = {k: v for k, v in fields.items() if v}
    if not filtered:
        return None

    filtered["type"] = "approximate"
    return cast(UserLocation, filtered)


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    if not trimmed:
        return None
    # Keep values reasonably small to avoid prompt bloat.
    return trimmed[:128]


__all__ = ["build_web_search_location", "UserLocation"]
