from __future__ import annotations

import json
import os
from collections.abc import Callable
from urllib.parse import urlparse

import httpx

from ..common import CLIError

_VAULT_PROBE_REQUEST: Callable[[str, dict[str, str]], httpx.Response] | None = None


def validate_plan_map(raw: str) -> dict[str, str]:
    text = (raw or "").strip()
    if not text:
        return {}

    parsed: dict[str, str]
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError:
        parsed = _parse_plan_map_csv(text)
    else:
        if not isinstance(loaded, dict):
            raise CLIError(
                "STRIPE_PRODUCT_PRICE_MAP must be a JSON object or comma-delimited list."
            )
        parsed = {str(key): str(value) for key, value in loaded.items()}

    normalized: dict[str, str] = {}
    for key, value in parsed.items():
        plan = key.strip()
        price = value.strip()
        if not plan or not price:
            raise CLIError(
                "Stripe plan map entries require non-empty plan codes and price IDs."
            )
        normalized[plan] = price
    return normalized


def _parse_plan_map_csv(text: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in text.split(","):
        entry = item.strip()
        if not entry:
            continue
        if "=" in entry:
            key, price = entry.split("=", 1)
        elif ":" in entry:
            key, price = entry.split(":", 1)
        else:
            raise CLIError(
                "Invalid STRIPE_PRODUCT_PRICE_MAP entry. Use key=value pairs or JSON."
            )
        parsed[key] = price
    if not parsed:
        raise CLIError("STRIPE_PRODUCT_PRICE_MAP must include at least one plan entry.")
    return parsed


def validate_redis_url(url: str, *, require_tls: bool, role: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"redis", "rediss"}:
        raise CLIError(f"{role} Redis URL must start with redis:// or rediss://")
    if not parsed.hostname:
        raise CLIError(f"{role} Redis URL is missing a hostname.")
    if require_tls and parsed.scheme != "rediss":
        raise CLIError(
            f"{role} Redis URL must use rediss:// (TLS) outside local environments."
        )
    if parsed.hostname not in {"localhost", "127.0.0.1"} and parsed.password is None:
        raise CLIError(f"{role} Redis URL should include an AUTH token for managed deployments.")


def normalize_logging_sink(value: str) -> str:
    options = {"stdout", "datadog", "otlp", "none"}
    normalized = value.strip().lower()
    if normalized not in options:
        raise CLIError(
            "Logging sink must be one of stdout, datadog, otlp, or none."
        )
    return normalized


def normalize_geoip_provider(value: str) -> str:
    options = {"none", "maxmind", "ip2location"}
    normalized = value.strip().lower()
    if normalized not in options:
        raise CLIError("GeoIP provider must be one of none, maxmind, ip2location.")
    return normalized


def parse_positive_int(value: str, *, field: str, minimum: int = 1) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise CLIError(f"{field} must be an integer.") from exc
    if parsed < minimum:
        raise CLIError(f"{field} must be at least {minimum}.")
    return parsed


def probe_vault_transit(
    *,
    base_url: str,
    token: str,
    key_name: str,
    request: Callable[[str, dict[str, str]], httpx.Response] | None = None,
) -> bool:
    if os.getenv("STARTER_CLI_SKIP_VAULT_PROBE", "false").lower() in {"1", "true", "yes"}:
        return True
    if not base_url or not token or not key_name:
        raise CLIError("Vault address, token, and transit key are required to verify connectivity.")
    target = f"{base_url.rstrip('/')}/v1/transit/keys/{key_name}"
    headers = {"X-Vault-Token": token}
    sender = request or _VAULT_PROBE_REQUEST or _default_vault_request
    response = sender(target, headers)
    if response.status_code >= 400:
        raise CLIError(
            f"Vault transit check failed ({response.status_code}): {response.text.strip()}"
        )
    return True


def _default_vault_request(url: str, headers: dict[str, str]) -> httpx.Response:
    with httpx.Client(timeout=5.0) as client:
        return client.get(url, headers=headers)


def set_vault_probe_request(
    factory: Callable[[str, dict[str, str]], httpx.Response] | None,
) -> None:
    global _VAULT_PROBE_REQUEST
    _VAULT_PROBE_REQUEST = factory


__all__ = [
    "normalize_geoip_provider",
    "normalize_logging_sink",
    "parse_positive_int",
    "probe_vault_transit",
    "validate_plan_map",
    "validate_redis_url",
    "set_vault_probe_request",
]
