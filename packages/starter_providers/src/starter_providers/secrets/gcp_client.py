"""GCP Secret Manager client helper."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from google.api_core import exceptions as gcp_exceptions
from google.auth import exceptions as auth_exceptions
from google.cloud import secretmanager


class GCPSecretManagerError(RuntimeError):
    """Raised when GCP Secret Manager operations fail."""


@dataclass(slots=True)
class GCPSecretManagerClient:
    project_id: str | None = None
    _client: secretmanager.SecretManagerServiceClient = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            self._client = secretmanager.SecretManagerServiceClient()
        except (auth_exceptions.GoogleAuthError, gcp_exceptions.GoogleAPICallError) as exc:
            raise GCPSecretManagerError(
                f"Failed to initialize GCP Secret Manager client: {exc}"
            ) from exc

    def get_secret_value(self, secret_id: str) -> str:
        value = self.get_secret_value_optional(secret_id)
        if value is None:
            raise GCPSecretManagerError(f"Secret {secret_id} was not found.")
        return value

    def get_secret_value_optional(self, secret_id: str) -> str | None:
        name = self._resolve_version_name(secret_id)
        try:
            response = self._client.access_secret_version(request={"name": name})
        except gcp_exceptions.NotFound:
            return None
        except (gcp_exceptions.GoogleAPICallError, auth_exceptions.GoogleAuthError) as exc:
            raise GCPSecretManagerError(f"Failed to read secret {secret_id}: {exc}") from exc

        payload = getattr(response, "payload", None)
        data = getattr(payload, "data", None)
        if data is None:
            raise GCPSecretManagerError(f"Secret {secret_id} has no payload data.")
        return data.decode("utf-8")

    def put_secret_value(self, secret_id: str, value: str) -> None:
        secret_name = self._resolve_secret_name(secret_id)
        try:
            self._client.add_secret_version(
                request={
                    "parent": secret_name,
                    "payload": {"data": value.encode("utf-8")},
                }
            )
            return
        except gcp_exceptions.NotFound:
            project_id, short_name = self._parse_secret_name(secret_name)
            try:
                self._client.create_secret(
                    request={
                        "parent": f"projects/{project_id}",
                        "secret_id": short_name,
                        "secret": {"replication": {"automatic": {}}},
                    }
                )
            except gcp_exceptions.AlreadyExists:
                pass
            except (gcp_exceptions.GoogleAPICallError, auth_exceptions.GoogleAuthError) as exc:
                raise GCPSecretManagerError(
                    f"Failed to create secret {secret_id}: {exc}"
                ) from exc
            try:
                self._client.add_secret_version(
                    request={
                        "parent": secret_name,
                        "payload": {"data": value.encode("utf-8")},
                    }
                )
                return
            except (gcp_exceptions.GoogleAPICallError, auth_exceptions.GoogleAuthError) as exc:
                raise GCPSecretManagerError(
                    f"Failed to write secret {secret_id}: {exc}"
                ) from exc
        except (gcp_exceptions.GoogleAPICallError, auth_exceptions.GoogleAuthError) as exc:
            raise GCPSecretManagerError(f"Failed to write secret {secret_id}: {exc}") from exc

    def describe_secret(self, secret_id: str) -> Any:
        name = self._resolve_secret_name(secret_id)
        try:
            return self._client.get_secret(request={"name": name})
        except (gcp_exceptions.GoogleAPICallError, auth_exceptions.GoogleAuthError) as exc:
            raise GCPSecretManagerError(f"Failed to describe secret {secret_id}: {exc}") from exc

    def _resolve_secret_name(self, secret_id: str) -> str:
        value = secret_id.strip()
        if value.startswith("projects/"):
            if "/versions/" in value:
                return value.split("/versions/")[0]
            return value
        if not self.project_id:
            raise GCPSecretManagerError(
                "GCP_SM_PROJECT_ID must be set when secret name is not fully qualified."
            )
        return f"projects/{self.project_id}/secrets/{value}"

    def _resolve_version_name(self, secret_id: str, *, version: str = "latest") -> str:
        value = secret_id.strip()
        if value.startswith("projects/") and "/versions/" in value:
            return value
        return f"{self._resolve_secret_name(value)}/versions/{version}"

    @staticmethod
    def _parse_secret_name(secret_name: str) -> tuple[str, str]:
        parts = secret_name.split("/")
        if len(parts) < 4 or parts[0] != "projects" or parts[2] != "secrets":
            raise GCPSecretManagerError(
                f"Invalid secret resource name: {secret_name}. Expected projects/<id>/secrets/<name>."
            )
        return parts[1], parts[3]


__all__ = ["GCPSecretManagerClient", "GCPSecretManagerError"]
