"""Thin boto3 wrapper for AWS Secrets Manager."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError


class AWSSecretsManagerError(RuntimeError):
    """Raised when AWS Secrets Manager calls fail."""


@dataclass(slots=True)
class AWSSecretsManagerClient:
    region: str
    profile: str | None = None
    access_key_id: str | None = None
    secret_access_key: str | None = None
    session_token: str | None = None
    _client: Any = field(init=False)

    def __post_init__(self) -> None:
        session = boto3.Session(
            profile_name=self.profile,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            aws_session_token=self.session_token,
            region_name=self.region,
        )
        self._client = session.client(
            "secretsmanager",
            config=BotoConfig(retries={"max_attempts": 3, "mode": "standard"}),
        )

    def get_secret_value(self, secret_id: str) -> str:
        value = self.get_secret_value_optional(secret_id)
        if value is None:
            raise AWSSecretsManagerError(f"Secret {secret_id} was not found.")
        return value

    def get_secret_value_optional(self, secret_id: str) -> str | None:
        try:
            response = self._client.get_secret_value(SecretId=secret_id)
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code")
            if code == "ResourceNotFoundException":
                return None
            raise AWSSecretsManagerError(f"Failed to read secret {secret_id}: {exc}") from exc
        except BotoCoreError as exc:  # pragma: no cover - boto handles details
            raise AWSSecretsManagerError(f"Failed to read secret {secret_id}: {exc}") from exc

        if "SecretString" in response and isinstance(response["SecretString"], str):
            return response["SecretString"]
        if "SecretBinary" in response:
            value = response["SecretBinary"]
            if isinstance(value, (bytes, bytearray)):  # noqa: UP038 - tuple required for isinstance
                return value.decode("utf-8")
        raise AWSSecretsManagerError(f"Secret {secret_id} has no string payload.")

    def put_secret_value(self, secret_id: str, value: str) -> None:
        try:
            self._client.put_secret_value(SecretId=secret_id, SecretString=value)
            return
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code")
            if code == "ResourceNotFoundException":
                if secret_id.startswith("arn:"):
                    raise AWSSecretsManagerError(
                        f"Secret {secret_id} does not exist; create it before writing."
                    ) from exc
                try:
                    self._client.create_secret(Name=secret_id, SecretString=value)
                    return
                except (BotoCoreError, ClientError) as inner_exc:
                    raise AWSSecretsManagerError(
                        f"Failed to create secret {secret_id}: {inner_exc}"
                    ) from inner_exc
            raise AWSSecretsManagerError(f"Failed to write secret {secret_id}: {exc}") from exc
        except BotoCoreError as exc:
            raise AWSSecretsManagerError(f"Failed to write secret {secret_id}: {exc}") from exc

    def describe_secret(self, secret_id: str) -> dict[str, Any]:
        try:
            response = self._client.describe_secret(SecretId=secret_id)
        except (BotoCoreError, ClientError) as exc:
            raise AWSSecretsManagerError(f"Failed to describe secret {secret_id}: {exc}") from exc
        return response


__all__ = ["AWSSecretsManagerClient", "AWSSecretsManagerError"]
