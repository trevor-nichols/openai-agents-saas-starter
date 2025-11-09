"""Lightweight user-agent classifier for session metadata."""

from __future__ import annotations

from app.domain.auth import SessionClientDetails

_BROWSER_MAP = [
    ("edg", "Edge"),
    ("brave", "Brave"),
    ("arc/", "Arc"),
    ("chrome", "Chrome"),
    ("safari", "Safari"),
    ("firefox", "Firefox"),
    ("trident", "Internet Explorer"),
    ("msie", "Internet Explorer"),
    ("opr", "Opera"),
]

_PLATFORM_MAP = [
    ("iphone", "iOS"),
    ("ipad", "iPadOS"),
    ("mac os x", "macOS"),
    ("macintosh", "macOS"),
    ("android", "Android"),
    ("windows nt", "Windows"),
    ("cros", "ChromeOS"),
    ("linux", "Linux"),
]


def summarize_user_agent(user_agent: str | None) -> SessionClientDetails:
    """Return coarse platform/browser/device hints without heavy dependencies."""

    if not user_agent:
        return SessionClientDetails()
    lowered = user_agent.lower()
    platform = _match_first(lowered, _PLATFORM_MAP)
    browser = _detect_browser(lowered)
    device = _detect_device_kind(lowered)
    return SessionClientDetails(platform=platform, browser=browser, device=device)


def _match_first(payload: str, candidates: list[tuple[str, str]]) -> str | None:
    for needle, value in candidates:
        if needle in payload:
            return value
    return None


def _detect_browser(payload: str) -> str | None:
    # Order matters: Chrome tokens include Safari, etc.
    for needle, label in _BROWSER_MAP:
        if needle in payload:
            if label == "Safari" and ("chrome" in payload or "crios" in payload):
                continue
            if label == "Chrome" and ("edg" in payload or "opr" in payload or "brave" in payload):
                continue
            return label
    return None


def _detect_device_kind(payload: str) -> str | None:
    if any(bot in payload for bot in ("bot", "spider", "crawl")):
        return "bot"
    if "ipad" in payload or "tablet" in payload:
        return "tablet"
    if any(token in payload for token in ("mobile", "iphone", "android")):
        return "mobile"
    return "desktop"
