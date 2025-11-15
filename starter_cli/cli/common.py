from __future__ import annotations

import base64
import json
import os
import time
import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import boto3
import httpx
from azure.identity import (
    ChainedTokenCredential,
    ClientSecretCredential,
    DefaultAzureCredential,
    ManagedIdentityCredential,
)
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv
from starter_shared.config import StarterSettingsProtocol, get_settings
from starter_shared.secrets.models import SecretsProviderLiteral

from .console import console


class CLIError(RuntimeError):
    """Base exception for CLI failures."""


_CLI_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _CLI_DIR.parent.parent
DEFAULT_ENV_FILES: tuple[Path, ...] = (
    PROJECT_ROOT / ".env.compose",
    PROJECT_ROOT / ".env",
    PROJECT_ROOT / ".env.local",
)
TELEMETRY_ENV = "STARTER_CLI_TELEMETRY_OPT_IN"


@dataclass(slots=True)
class CLIContext:
    project_root: Path = PROJECT_ROOT
    env_files: tuple[Path, ...] = DEFAULT_ENV_FILES
    loaded_env_files: list[Path] = field(default_factory=list)
    settings: StarterSettingsProtocol | None = None

    def load_environment(self, *, verbose: bool = True) -> None:
        """Load environment variables from configured files."""
        self.loaded_env_files.clear()
        for env_file in self.env_files:
            if not env_file.exists():
                continue
            load_dotenv(env_file, override=True)
            self.loaded_env_files.append(env_file)
            if verbose:
                console.info(f"Loaded environment from {env_file}", topic="env")

    def optional_settings(self) -> StarterSettingsProtocol | None:
        """Attempt to load the FastAPI settings module."""
        if self.settings is not None:
            return self.settings
        try:
            self.settings = get_settings()
        except Exception:
            return None
        return self.settings

    def require_settings(self) -> StarterSettingsProtocol:
        """Load settings and raise CLIError if configuration is invalid."""
        settings = self.optional_settings()
        if settings is None:
            raise CLIError(
                "Unable to load application settings. "
                "Ensure .env values are present or pass --env-file explicitly."
            )
        return settings


def build_context(*, env_files: Sequence[Path] | None = None) -> CLIContext:
    if env_files:
        unique_files = tuple(dict.fromkeys(env_files))  # preserve order, remove duplicates
    else:
        unique_files = DEFAULT_ENV_FILES
    return CLIContext(env_files=unique_files)


def iter_env_files(paths: Iterable[str]) -> list[Path]:
    return [Path(path).expanduser().resolve() for path in paths]


def build_vault_headers(
    request_payload: dict[str, Any],
    settings: StarterSettingsProtocol | None,
) -> tuple[str, dict[str, str]]:
    """
    Build the Authorization header + payload metadata for Vault-signed requests.

    When Vault configuration is unavailable (dev-local), we fall back to the
    legacy "dev-local" bearer token scheme to preserve local workflows.
    """

    dev_mode = os.getenv("AUTH_CLI_DEV_AUTH_MODE", "vault").lower() == "local"
    if dev_mode:
        return "Bearer dev-local", {}

    envelope = _build_vault_envelope(request_payload)
    payload_json = json.dumps(envelope, separators=(",", ":"))
    payload_bytes = payload_json.encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")

    provider = (
        settings.secrets_provider if settings else SecretsProviderLiteral.VAULT_DEV
    )

    if provider in (SecretsProviderLiteral.VAULT_DEV, SecretsProviderLiteral.VAULT_HCP):
        if not settings or not settings.vault_addr or not settings.vault_token:
            return "Bearer dev-local", {}
        signature = _vault_sign_payload(
            base_url=settings.vault_addr,
            token=settings.vault_token,
            key_name=settings.vault_transit_key,
            payload_b64=payload_b64,
        )
    else:
        signature = _sign_with_hmac_provider(
            provider=provider,
            payload_bytes=payload_bytes,
            settings=settings,
        )

    headers = {"X-Vault-Payload": payload_b64}
    return f"Bearer vault:{signature}", headers


def _build_vault_envelope(request_payload: dict[str, Any]) -> dict[str, Any]:
    now = int(time.time())
    envelope: dict[str, Any] = {
        "iss": "vault-transit",
        "aud": ["auth-service"],
        "sub": "service-account-cli",
        "account": request_payload.get("account"),
        "tenant_id": request_payload.get("tenant_id"),
        "scopes": request_payload.get("scopes", []),
        "nonce": uuid.uuid4().hex,
        "iat": now,
        "exp": now + 300,
    }

    fingerprint = request_payload.get("fingerprint")
    if fingerprint:
        envelope["fingerprint"] = fingerprint

    lifetime = request_payload.get("lifetime_minutes")
    if lifetime is not None:
        envelope["lifetime_minutes"] = lifetime

    return envelope


def _vault_sign_payload(
    *,
    base_url: str,
    token: str,
    key_name: str,
    payload_b64: str,
) -> str:
    url = f"{base_url.rstrip('/')}/v1/transit/sign/{key_name}"
    headers = {"X-Vault-Token": token}
    body = {"input": payload_b64, "signature_algorithm": "sha2-256"}

    with httpx.Client(timeout=5.0) as client:
        response = client.post(url, json=body, headers=headers)

    if response.status_code >= 400:
        raise CLIError(f"Vault sign failed ({response.status_code}): {response.text}")

    data = response.json()
    signature = data.get("data", {}).get("signature")
    if not signature:
        raise CLIError("Vault sign response missing signature.")

    return signature


def _sign_with_hmac_provider(
    *,
    provider: SecretsProviderLiteral,
    payload_bytes: bytes,
    settings: StarterSettingsProtocol | None,
) -> str:
    if settings is None:
        raise CLIError("Application settings unavailable; cannot sign payload.")
    if provider in (
        SecretsProviderLiteral.INFISICAL_CLOUD,
        SecretsProviderLiteral.INFISICAL_SELF_HOST,
    ):
        secret = _fetch_infisical_secret(settings)
    elif provider is SecretsProviderLiteral.AWS_SM:
        secret = _fetch_aws_secret(settings)
    elif provider is SecretsProviderLiteral.AZURE_KV:
        secret = _fetch_azure_secret(settings)
    else:
        raise CLIError(f"Unsupported secrets provider: {provider.value}")

    import hmac
    from hashlib import sha256

    signature = hmac.new(
        secret.encode("utf-8"),
        payload_bytes,
        sha256,
    ).hexdigest()
    return signature


def _fetch_infisical_secret(settings: StarterSettingsProtocol) -> str:
    inf = settings.infisical_settings
    if not (
        inf.base_url
        and inf.service_token
        and inf.project_id
        and inf.environment
        and inf.signing_secret_name
    ):
        raise CLIError("Infisical configuration is incomplete; rerun secrets onboarding.")

    params = {
        "environment": inf.environment,
        "workspaceId": inf.project_id,
        "type": "shared",
        "path": inf.secret_path or "/",
    }
    url = f"{inf.base_url.rstrip('/')}/api/v4/secrets/{inf.signing_secret_name}"
    headers = {"Authorization": f"Bearer {inf.service_token}"}
    with httpx.Client(timeout=5.0, verify=inf.ca_bundle_path or True) as client:
        response = client.get(url, headers=headers, params=params)
    if response.status_code >= 400:
        raise CLIError(f"Infisical secret fetch failed ({response.status_code}): {response.text}")
    payload = response.json()
    secret = payload.get("secret", {}).get("secretValue")
    if not isinstance(secret, str):
        raise CLIError("Infisical response missing secret value.")
    return secret


def _fetch_aws_secret(settings: StarterSettingsProtocol) -> str:
    aws = settings.aws_settings
    if not (aws.region and aws.signing_secret_arn):
        raise CLIError("AWS configuration is incomplete; rerun secrets onboarding.")
    session = boto3.Session(
        profile_name=aws.profile,
        aws_access_key_id=aws.access_key_id,
        aws_secret_access_key=aws.secret_access_key,
        aws_session_token=aws.session_token,
        region_name=aws.region,
    )
    client = session.client("secretsmanager")
    try:
        response = client.get_secret_value(SecretId=aws.signing_secret_arn)
    except Exception as exc:  # pragma: no cover - boto handles detail
        raise CLIError(f"AWS secret fetch failed: {exc}") from exc
    if "SecretString" in response and isinstance(response["SecretString"], str):
        return response["SecretString"]
    if "SecretBinary" in response:
        value = response["SecretBinary"]
        if isinstance(value, (bytes, bytearray)):  # noqa: UP038
            return value.decode("utf-8")
    raise CLIError("AWS secret missing string payload.")


def _fetch_azure_secret(settings: StarterSettingsProtocol) -> str:
    az = settings.azure_settings
    if not (az.vault_url and az.signing_secret_name):
        raise CLIError("Azure Key Vault configuration is incomplete; rerun secrets onboarding.")

    credentials = []
    if az.tenant_id and az.client_id and az.client_secret:
        credentials.append(
            ClientSecretCredential(
                tenant_id=az.tenant_id,
                client_id=az.client_id,
                client_secret=az.client_secret,
            )
        )
    if az.managed_identity_client_id:
        credentials.append(
            ManagedIdentityCredential(client_id=az.managed_identity_client_id)
        )
    credentials.append(DefaultAzureCredential(exclude_interactive_browser_credential=True))
    credential = (
        credentials[0]
        if len(credentials) == 1
        else ChainedTokenCredential(*credentials)
    )
    client = SecretClient(vault_url=az.vault_url, credential=credential)
    try:
        secret = client.get_secret(az.signing_secret_name)
    except Exception as exc:  # pragma: no cover - azure sdk handles detail
        raise CLIError(f"Azure Key Vault secret fetch failed: {exc}") from exc
    if not secret.value:
        raise CLIError("Azure Key Vault secret has no value.")
    return secret.value
