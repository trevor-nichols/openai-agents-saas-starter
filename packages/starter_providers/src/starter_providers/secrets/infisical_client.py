"""HTTP client for Infisical secret retrieval and mutation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


class InfisicalAPIError(RuntimeError):
    """Raised when Infisical responds with an error."""


@dataclass(slots=True)
class InfisicalAPIClient:
    base_url: str
    service_token: str
    project_id: str
    environment: str
    secret_path: str
    ca_bundle_path: str | None = None
    timeout: float = 5.0
    transport: httpx.BaseTransport | None = None

    def _client(self) -> httpx.Client:
        verify: bool | str = self.ca_bundle_path or True
        return httpx.Client(
            timeout=self.timeout,
            verify=verify,
            transport=self.transport,
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}{path}"
        headers = {"Authorization": f"Bearer {self.service_token}"}

        with self._client() as client:
            response = client.request(method, url, headers=headers, params=params, json=payload)

        if response.status_code == 404:
            raise KeyError("Secret not found")
        if response.status_code >= 400:
            raise InfisicalAPIError(
                f"Infisical request failed ({response.status_code}): {response.text}"
            )

        payload = response.json()
        if not isinstance(payload, dict):
            raise InfisicalAPIError("Unexpected Infisical response payload.")
        return payload

    def get_secret(self, name: str) -> str | None:
        params = {
            "environment": self.environment,
            "workspaceId": self.project_id,
            "type": "shared",
            "path": self.secret_path or "/",
        }
        try:
            payload = self._request("GET", f"/api/v4/secrets/{name}", params=params)
        except KeyError:
            return None

        secret = payload.get("secret")
        if isinstance(secret, dict):
            value = secret.get("secretValue")
            if isinstance(value, str):
                return value
        raise InfisicalAPIError("Infisical secret response missing secretValue.")

    def set_secret(self, name: str, value: str) -> None:
        payload = {
            "type": "shared",
            "environment": self.environment,
            "projectId": self.project_id,
            "secretPath": self.secret_path or "/",
            "secretValue": value,
            "skipMultilineEncoding": True,
        }
        try:
            self._request("PATCH", f"/api/v4/secrets/{name}", payload=payload)
            return
        except KeyError:
            pass

        try:
            self._request("POST", f"/api/v4/secrets/{name}", payload=payload)
        except KeyError as exc:  # pragma: no cover - unexpected create 404
            raise InfisicalAPIError("Infisical secret create failed.") from exc


__all__ = ["InfisicalAPIClient", "InfisicalAPIError"]
