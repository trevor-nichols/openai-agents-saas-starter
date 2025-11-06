"""Prometheus metrics used across the application."""

from __future__ import annotations

from prometheus_client import Counter

JWKS_REQUESTS_TOTAL = Counter(
    "jwks_requests_total",
    "Total number of JWKS responses served.",
)

JWKS_NOT_MODIFIED_TOTAL = Counter(
    "jwks_not_modified_total",
    "Total number of JWKS requests answered with HTTP 304.",
)
