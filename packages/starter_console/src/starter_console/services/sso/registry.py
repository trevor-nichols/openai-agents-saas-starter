from __future__ import annotations

from dataclasses import dataclass

from starter_console.core import CLIError

from .config import normalize_provider_key
from .constants import (
    AUTH0_DISCOVERY_TEMPLATE,
    AUTH0_ISSUER_TEMPLATE,
    AUTH0_PROVIDER_KEY,
    AZURE_DISCOVERY_TEMPLATE,
    AZURE_ISSUER_TEMPLATE,
    AZURE_PROVIDER_KEY,
    DEFAULT_AUTO_PROVISION_POLICY,
    DEFAULT_ROLE,
    DEFAULT_SCOPE_MODE,
    DEFAULT_SCOPES,
    DEFAULT_TOKEN_AUTH_METHOD,
    GOOGLE_DISCOVERY_URL,
    GOOGLE_ISSUER_URL,
    GOOGLE_PROVIDER_KEY,
    OKTA_DISCOVERY_TEMPLATE,
    OKTA_ISSUER_TEMPLATE,
    OKTA_PROVIDER_KEY,
)


@dataclass(frozen=True, slots=True)
class SsoProviderPreset:
    key: str
    label: str
    description: str
    issuer_url: str
    discovery_url: str
    scopes: tuple[str, ...] = DEFAULT_SCOPES
    token_auth_method: str = DEFAULT_TOKEN_AUTH_METHOD
    pkce_required: bool = True
    auto_provision_policy: str = DEFAULT_AUTO_PROVISION_POLICY
    default_role: str = DEFAULT_ROLE
    scope_mode: str = DEFAULT_SCOPE_MODE


GOOGLE_PRESET = SsoProviderPreset(
    key=GOOGLE_PROVIDER_KEY,
    label="Google",
    description="Google Workspace / Cloud Identity",
    issuer_url=GOOGLE_ISSUER_URL,
    discovery_url=GOOGLE_DISCOVERY_URL,
)

AZURE_PRESET = SsoProviderPreset(
    key=AZURE_PROVIDER_KEY,
    label="Azure Entra ID",
    description="Microsoft Entra ID (Azure AD) tenants",
    issuer_url=AZURE_ISSUER_TEMPLATE,
    discovery_url=AZURE_DISCOVERY_TEMPLATE,
)

OKTA_PRESET = SsoProviderPreset(
    key=OKTA_PROVIDER_KEY,
    label="Okta",
    description="Okta orgs using the default authorization server",
    issuer_url=OKTA_ISSUER_TEMPLATE,
    discovery_url=OKTA_DISCOVERY_TEMPLATE,
)

AUTH0_PRESET = SsoProviderPreset(
    key=AUTH0_PROVIDER_KEY,
    label="Auth0",
    description="Auth0 tenants",
    issuer_url=AUTH0_ISSUER_TEMPLATE,
    discovery_url=AUTH0_DISCOVERY_TEMPLATE,
)

CUSTOM_PRESET = SsoProviderPreset(
    key="custom",
    label="Custom OIDC",
    description="Any OIDC provider with issuer + discovery endpoints",
    issuer_url="",
    discovery_url="",
)

PRESETS: tuple[SsoProviderPreset, ...] = (
    GOOGLE_PRESET,
    AZURE_PRESET,
    OKTA_PRESET,
    AUTH0_PRESET,
    CUSTOM_PRESET,
)

_PRESET_BY_KEY = {preset.key: preset for preset in PRESETS}


def list_presets() -> tuple[SsoProviderPreset, ...]:
    return PRESETS


def get_preset(key: str) -> SsoProviderPreset:
    normalized = normalize_provider_key(key, allow_reserved=True)
    preset = _PRESET_BY_KEY.get(normalized)
    if preset is None:
        raise CLIError(f"Unknown SSO provider preset: {key}")
    return preset


def find_preset(key: str) -> SsoProviderPreset | None:
    normalized = normalize_provider_key(key, allow_reserved=True)
    return _PRESET_BY_KEY.get(normalized)


def is_custom_preset(preset: SsoProviderPreset) -> bool:
    return preset.key == CUSTOM_PRESET.key


def preset_defaults(preset: SsoProviderPreset) -> dict[str, str]:
    return {
        "issuer_url": preset.issuer_url,
        "discovery_url": preset.discovery_url,
        "scopes": ",".join(preset.scopes),
        "token_auth_method": preset.token_auth_method,
        "auto_provision_policy": preset.auto_provision_policy,
        "default_role": preset.default_role,
        "scope_mode": preset.scope_mode,
        "pkce_required": "true" if preset.pkce_required else "false",
    }


__all__ = [
    "AUTH0_PRESET",
    "AZURE_PRESET",
    "CUSTOM_PRESET",
    "GOOGLE_PRESET",
    "OKTA_PRESET",
    "SsoProviderPreset",
    "find_preset",
    "get_preset",
    "is_custom_preset",
    "list_presets",
    "preset_defaults",
]
