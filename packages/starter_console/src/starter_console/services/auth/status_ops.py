from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx

from starter_console.core import CLIError

DEFAULT_STATUS_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_STATUS_TIMEOUT = 10.0


@dataclass(frozen=True, slots=True)
class StatusApiConfig:
    base_url: str
    token: str
    timeout: float = DEFAULT_STATUS_TIMEOUT


@dataclass(frozen=True, slots=True)
class StatusSubscription:
    id: str
    status: str
    target_masked: str
    channel: str
    severity_filter: str
    tenant_id: str | None


@dataclass(frozen=True, slots=True)
class StatusSubscriptionList:
    items: list[StatusSubscription]
    next_cursor: str | None


@dataclass(frozen=True, slots=True)
class StatusIncidentResendResult:
    incident_id: str
    dispatched: int


class StatusOpsClient:
    def __init__(self, config: StatusApiConfig) -> None:
        self._config = config

    @classmethod
    def from_env(cls) -> StatusOpsClient:
        return cls(load_status_api_config())

    def list_subscriptions(
        self,
        *,
        limit: int = 50,
        cursor: str | None = None,
        tenant_id: str | None = None,
    ) -> StatusSubscriptionList:
        params: dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if tenant_id:
            params["tenant_id"] = tenant_id
        response = self._request(
            method="GET",
            path="/api/v1/status/subscriptions",
            params=params,
        )
        payload = response.json()
        items = [
            StatusSubscription(
                id=str(item.get("id")),
                status=str(item.get("status")),
                target_masked=str(item.get("target_masked")),
                channel=str(item.get("channel")),
                severity_filter=str(item.get("severity_filter")),
                tenant_id=str(item.get("tenant_id")) if item.get("tenant_id") else None,
            )
            for item in payload.get("items", [])
        ]
        return StatusSubscriptionList(items=items, next_cursor=payload.get("next_cursor"))

    def revoke_subscription(self, subscription_id: str) -> None:
        self._request(
            method="DELETE",
            path=f"/api/v1/status/subscriptions/{subscription_id}",
        )

    def resend_incident(
        self,
        *,
        incident_id: str,
        severity: str = "major",
        tenant_id: str | None = None,
    ) -> StatusIncidentResendResult:
        payload: dict[str, Any] = {"severity": severity}
        if tenant_id:
            payload["tenant_id"] = tenant_id
        response = self._request(
            method="POST",
            path=f"/api/v1/status/incidents/{incident_id}/resend",
            json_body=payload,
        )
        body = response.json()
        dispatched = int(body.get("dispatched", 0))
        return StatusIncidentResendResult(incident_id=incident_id, dispatched=dispatched)

    def _request(
        self,
        *,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> httpx.Response:
        url = f"{self._config.base_url.rstrip('/')}{path}"
        headers = {"Authorization": f"Bearer {self._config.token}"}
        with httpx.Client(timeout=self._config.timeout) as client:
            response = client.request(method, url, params=params, json=json_body, headers=headers)
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail")
            except Exception:
                detail = response.text
            raise CLIError(f"Status API call failed ({response.status_code}): {detail}")
        return response


def load_status_api_config() -> StatusApiConfig:
    token = os.getenv("STATUS_API_TOKEN")
    if not token:
        raise CLIError("STATUS_API_TOKEN is required to call status APIs.")
    base_url = os.getenv(
        "STATUS_API_BASE_URL",
        os.getenv("AUTH_CLI_BASE_URL", DEFAULT_STATUS_BASE_URL),
    )
    return StatusApiConfig(base_url=base_url, token=token, timeout=DEFAULT_STATUS_TIMEOUT)


__all__ = [
    "DEFAULT_STATUS_BASE_URL",
    "DEFAULT_STATUS_TIMEOUT",
    "StatusApiConfig",
    "StatusIncidentResendResult",
    "StatusOpsClient",
    "StatusSubscription",
    "StatusSubscriptionList",
    "load_status_api_config",
]
