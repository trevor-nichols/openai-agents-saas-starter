"""Signing helpers for CLI interactions with backend services."""

from __future__ import annotations

import base64
import json
import os
import time
import uuid
from typing import Any

import httpx
from starter_contracts.config import StarterSettingsProtocol
from starter_contracts.secrets.models import SecretsProviderLiteral
from starter_providers.secrets import AWSSecretsManagerClient, AzureKeyVaultClient

from ....core.constants import SAFE_ENVIRONMENTS
from ....core.exceptions import CLIError

_VAULT_PROVIDERS = {
    SecretsProviderLiteral.VAULT_DEV,
    SecretsProviderLiteral.VAULT_HCP,
}


def build_vault_headers(
    request_payload: dict[str, Any],
    settings: StarterSettingsProtocol | None,
) -> tuple[str, dict[str, str]]:
    """Build Authorization headers for Vault/HMAC-backed signing."""

    dev_mode = os.getenv("AUTH_CLI_DEV_AUTH_MODE", "vault").lower() == "demo"
    hardened = _requires_vault_verification(settings)

    if dev_mode and hardened:
        raise CLIError(
            "AUTH_CLI_DEV_AUTH_MODE=demo is not permitted when Vault verification is required."
        )
    if dev_mode:
        return "Bearer dev-demo", {}

    if settings is None and not hardened:
        return "Bearer dev-demo", {}
    if settings is None and hardened:
        raise CLIError(
            "Application settings unavailable; cannot sign service-account requests in "
            "staging/production. Load env files or rerun the setup wizard."
        )

    assert settings is not None
    provider = settings.secrets_provider

    envelope = _build_vault_envelope(request_payload)
    payload_json = json.dumps(envelope, separators=(",", ":"))
    payload_bytes = payload_json.encode("utf-8")
    # Keep padding so Vault transit can decode with strict base64 requirements
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("utf-8")

    if provider in _VAULT_PROVIDERS:
        config = _resolve_vault_config(settings)
        if config is None:
            missing = _missing_vault_config(settings)
            if hardened:
                joined = ", ".join(missing)
                raise CLIError(
                    "Vault signing requires complete configuration. "
                    f"Set {joined} or run the setup wizard."
                )
            return "Bearer dev-demo", {}
        base_url, token, key_name = config
        signature = _vault_sign_payload(
            base_url=base_url,
            token=token,
            key_name=key_name,
            payload_b64=payload_b64,
            namespace=settings.vault_namespace,
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
    namespace: str | None = None,
) -> str:
    url = f"{base_url.rstrip('/')}/v1/transit/sign/{key_name}"
    headers = {"X-Vault-Token": token}
    if namespace:
        headers["X-Vault-Namespace"] = namespace
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


def _requires_vault_verification(settings: StarterSettingsProtocol | None) -> bool:
    env = (settings.environment if settings else os.getenv("ENVIRONMENT", "development")).lower()
    debug = (
        settings.debug
        if settings is not None
        else os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"}
    )
    enabled_flag = (
        settings.vault_verify_enabled
        if settings is not None
        else os.getenv("VAULT_VERIFY_ENABLED", "false").lower() in {"1", "true", "yes"}
    )
    return enabled_flag or (env not in SAFE_ENVIRONMENTS and not debug)


def _missing_vault_config(settings: StarterSettingsProtocol) -> list[str]:
    missing: list[str] = []
    if not settings.vault_addr:
        missing.append("VAULT_ADDR")
    if not settings.vault_token:
        missing.append("VAULT_TOKEN")
    if not settings.vault_transit_key:
        missing.append("VAULT_TRANSIT_KEY")
    return missing


def _resolve_vault_config(
    settings: StarterSettingsProtocol,
) -> tuple[str, str, str] | None:
    if settings.vault_addr and settings.vault_token and settings.vault_transit_key:
        return settings.vault_addr, settings.vault_token, settings.vault_transit_key
    return None


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
    client = AWSSecretsManagerClient(
        region=aws.region,
        profile=aws.profile,
        access_key_id=aws.access_key_id,
        secret_access_key=aws.secret_access_key,
        session_token=aws.session_token,
    )
    try:
        value = client.get_secret_value(aws.signing_secret_arn)
    except Exception as exc:  # pragma: no cover
        raise CLIError(f"AWS secret fetch failed: {exc}") from exc
    return value


def _fetch_azure_secret(settings: StarterSettingsProtocol) -> str:
    az = settings.azure_settings
    if not (az.vault_url and az.signing_secret_name):
        raise CLIError("Azure Key Vault configuration is incomplete; rerun secrets onboarding.")
    client = AzureKeyVaultClient(
        vault_url=az.vault_url,
        tenant_id=az.tenant_id,
        client_id=az.client_id,
        client_secret=az.client_secret,
        managed_identity_client_id=az.managed_identity_client_id,
    )
    try:
        secret = client.get_secret(az.signing_secret_name)
    except Exception as exc:  # pragma: no cover
        raise CLIError(f"Azure Key Vault secret fetch failed: {exc}") from exc
    return secret


__all__ = ["build_vault_headers"]
