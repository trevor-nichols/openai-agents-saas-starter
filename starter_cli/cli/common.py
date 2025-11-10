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

import httpx
from dotenv import load_dotenv
from starter_shared.config import StarterSettingsProtocol, get_settings

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
    if dev_mode or not settings or not settings.vault_addr or not settings.vault_token:
        return "Bearer dev-local", {}

    payload_json = json.dumps(_build_vault_envelope(request_payload), separators=(",", ":"))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("utf-8").rstrip("=")

    signature = _vault_sign_payload(
        base_url=settings.vault_addr,
        token=settings.vault_token,
        key_name=settings.vault_transit_key,
        payload_b64=payload_b64,
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

    if signature.startswith("vault:v1:"):
        signature = signature.split(":", 2)[-1]
    return signature
