"""URL filter guardrail check implementation."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from app.guardrails._shared.specs import GuardrailCheckResult

# URL extraction regex pattern
URL_PATTERN = re.compile(
    r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+"
    r"(?:/[-\w%!$&'()*+,.:;=@~#/?]*)?",
    re.IGNORECASE,
)


def extract_urls(text: str) -> list[str]:
    """Extract all URLs from text content.

    Args:
        text: The text to scan for URLs.

    Returns:
        List of extracted URL strings.
    """
    return URL_PATTERN.findall(text)


def get_domain(url: str) -> str:
    """Extract the domain from a URL.

    Args:
        url: The URL to parse.

    Returns:
        The domain portion of the URL.
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return ""


def domain_matches(
    domain: str,
    pattern: str,
    check_subdomains: bool,
) -> bool:
    """Check if a domain matches a pattern.

    Args:
        domain: The domain to check.
        pattern: The pattern to match against.
        check_subdomains: Whether to match subdomains.

    Returns:
        True if the domain matches the pattern.
    """
    domain = domain.lower()
    pattern = pattern.lower()

    # Remove protocol if present in pattern
    if "://" in pattern:
        pattern = urlparse(pattern).netloc

    if not pattern:
        return False

    if domain == pattern:
        return True

    if check_subdomains and domain.endswith("." + pattern):
        return True

    return False


async def run_check(
    content: str,
    config: dict[str, Any],
    *,
    conversation_history: list[dict[str, str]] | None = None,
    context: dict[str, Any] | None = None,
) -> GuardrailCheckResult:
    """Execute URL filter check.

    Args:
        content: The text content to check.
        config: Validated configuration dictionary.
        conversation_history: Not used for URL filter.
        context: Runtime context (not used).

    Returns:
        GuardrailCheckResult indicating if blocked URLs were found.
    """
    allow_list: list[str] = config.get("url_allow_list", [])
    block_list: list[str] = config.get("url_block_list", [])
    check_subdomains: bool = config.get("check_subdomains", True)
    extract: bool = config.get("extract_urls", True)

    # Extract URLs from content
    if extract:
        urls = extract_urls(content)
    else:
        # Treat entire content as a single URL
        urls = [content.strip()] if content.strip() else []

    if not urls:
        return GuardrailCheckResult(
            tripwire_triggered=False,
            info={
                "guardrail_name": "URL Filter",
                "flagged": False,
                "urls_found": 0,
                "blocked_urls": [],
                "allowed_urls": [],
            },
        )

    blocked_urls: list[str] = []
    allowed_urls: list[str] = []

    for url in urls:
        domain = get_domain(url)
        if not domain:
            continue

        # Check block list first
        is_blocked = any(
            domain_matches(domain, pattern, check_subdomains)
            for pattern in block_list
        )
        if is_blocked:
            blocked_urls.append(url)
            continue

        # If allow list is specified, URL must match
        if allow_list:
            is_allowed = any(
                domain_matches(domain, pattern, check_subdomains)
                for pattern in allow_list
            )
            if is_allowed:
                allowed_urls.append(url)
            else:
                blocked_urls.append(url)
        else:
            # No allow list means all non-blocked URLs are allowed
            allowed_urls.append(url)

    flagged = len(blocked_urls) > 0

    return GuardrailCheckResult(
        tripwire_triggered=flagged,
        info={
            "guardrail_name": "URL Filter",
            "flagged": flagged,
            "urls_found": len(urls),
            "blocked_urls": blocked_urls,
            "allowed_urls": allowed_urls,
            "allow_list_configured": len(allow_list) > 0,
            "block_list_configured": len(block_list) > 0,
        },
    )
