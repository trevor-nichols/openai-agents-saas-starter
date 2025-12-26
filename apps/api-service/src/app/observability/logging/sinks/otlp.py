"""OTLP JSON-over-HTTP sink."""

from starter_contracts.observability.logging.sinks.otlp import (
    OTLPHTTPLogHandler,
    _to_otlp_payload,
    build_otlp_sink,
    parse_headers,
)

__all__ = ["OTLPHTTPLogHandler", "build_otlp_sink", "parse_headers", "_to_otlp_payload"]
