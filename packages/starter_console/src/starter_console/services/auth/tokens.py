from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import httpx

from starter_console.core import CLIContext, CLIError
from starter_console.services.auth.security import build_vault_headers

DEFAULT_OUTPUT_FORMAT = "json"
DEFAULT_BASE_URL = "http://127.0.0.1:8000"
VALID_OUTPUT_FORMATS = {"json", "text", "env"}


@dataclass(frozen=True, slots=True)
class IssueServiceAccountRequest:
    account: str
    scopes: list[str]
    tenant_id: str | None
    lifetime_minutes: int | None
    fingerprint: str | None
    force: bool


def parse_scopes(raw_scopes: str) -> list[str]:
    scopes = [scope.strip() for scope in raw_scopes.split(",") if scope.strip()]
    if not scopes:
        raise CLIError("At least one scope must be provided via --scopes.")
    return scopes


def resolve_output_format() -> str:
    value = os.getenv("AUTH_CLI_OUTPUT", DEFAULT_OUTPUT_FORMAT).lower()
    if value not in VALID_OUTPUT_FORMATS:
        raise CLIError(
            f"AUTH_CLI_OUTPUT must be one of {sorted(VALID_OUTPUT_FORMATS)} (got '{value}')."
        )
    return value


def resolve_base_url() -> str:
    return os.getenv("API_BASE_URL", DEFAULT_BASE_URL)


def issue_service_account(
    *,
    ctx: CLIContext,
    base_url: str,
    request: IssueServiceAccountRequest,
) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/v1/auth/service-accounts/issue"
    settings = ctx.optional_settings()
    payload = {
        "account": request.account,
        "scopes": request.scopes,
        "tenant_id": request.tenant_id,
        "lifetime_minutes": request.lifetime_minutes,
        "fingerprint": request.fingerprint,
        "force": request.force,
    }
    auth_header, extra_headers = build_vault_headers(payload, settings)
    headers = {"Authorization": auth_header, **extra_headers}

    with httpx.Client(timeout=10.0) as client:
        response = client.post(url, json=payload, headers=headers)

    if response.status_code >= 400:
        try:
            body = response.json()
            detail = body.get("detail") or body.get("message") or body.get("error")
        except Exception:
            detail = response.text
        raise CLIError(f"Issuance failed ({response.status_code}): {detail}")

    document = response.json()
    ctx.console.success(
        "Service-account token issued.",
        topic="auth",
        stream=ctx.console.err_stream,
    )
    return document


def render_issue_output(data: dict[str, Any], fmt: str) -> str:
    if fmt == "json":
        return json.dumps(data, indent=2)
    if fmt == "env":
        return "\n".join([f"AUTH_REFRESH_TOKEN={data['refresh_token']}"])

    lines = [
        f"Account: {data.get('account')}",
        f"Scopes: {', '.join(data.get('scopes', []))}",
        f"Issued At: {data.get('issued_at')}",
        f"Expires At: {data.get('expires_at')}",
        f"Tenant ID: {data.get('tenant_id') or 'global'}",
        f"Token Use: {data.get('token_use')}",
        f"Key ID: {data.get('kid')}",
        "",
        "Refresh Token:",
        data.get("refresh_token", ""),
    ]
    return "\n".join(lines)


__all__ = [
    "DEFAULT_BASE_URL",
    "DEFAULT_OUTPUT_FORMAT",
    "IssueServiceAccountRequest",
    "issue_service_account",
    "parse_scopes",
    "render_issue_output",
    "resolve_base_url",
    "resolve_output_format",
]
