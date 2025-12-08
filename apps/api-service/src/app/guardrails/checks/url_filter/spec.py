"""URL filter guardrail specification."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.guardrails._shared.specs import GuardrailSpec


class URLFilterConfig(BaseModel):
    """Configuration for URL filter guardrail.

    Attributes:
        url_allow_list: List of allowed URL patterns/domains. If set, only
            URLs matching these patterns are permitted.
        url_block_list: List of blocked URL patterns/domains. URLs matching
            these patterns are rejected.
        check_subdomains: Whether to match subdomains (e.g., "example.com"
            matches "sub.example.com").
        extract_urls: Whether to extract and check URLs from text content.
    """

    url_allow_list: list[str] = Field(
        default_factory=list,
        description="List of allowed URL patterns/domains",
    )
    url_block_list: list[str] = Field(
        default_factory=list,
        description="List of blocked URL patterns/domains",
    )
    check_subdomains: bool = Field(
        default=True,
        description="Whether to match subdomains",
    )
    extract_urls: bool = Field(
        default=True,
        description="Whether to extract URLs from text content",
    )


def get_guardrail_spec() -> GuardrailSpec:
    """Return the URL filter guardrail specification."""
    return GuardrailSpec(
        key="url_filter",
        display_name="URL Filter",
        description=(
            "Filters URLs against allow/block lists. Can be used to restrict "
            "which external resources an agent can reference or recommend."
        ),
        stage="output",
        engine="regex",
        config_schema=URLFilterConfig,
        check_fn_path="app.guardrails.checks.url_filter.check:run_check",
        uses_conversation_history=False,
        default_config={
            "url_allow_list": [],
            "url_block_list": [],
            "check_subdomains": True,
            "extract_urls": True,
        },
        supports_masking=False,
        tripwire_on_error=False,
    )
