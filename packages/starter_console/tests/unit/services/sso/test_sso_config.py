from __future__ import annotations

import pytest
from starter_console.core import CLIError
from starter_console.services.sso.config import (
    build_config_from_env,
    normalize_provider_key,
    parse_provider_list,
    resolve_enabled_providers,
)
from starter_console.services.sso.constants import GOOGLE_PROVIDER_KEY


def _base_env() -> dict[str, str]:
    return {
        "SSO_GOOGLE_ENABLED": "true",
        "SSO_GOOGLE_SCOPE": "global",
        "SSO_GOOGLE_ISSUER_URL": "https://accounts.google.com",
        "SSO_GOOGLE_CLIENT_ID": "client-id",
        "SSO_GOOGLE_CLIENT_SECRET": "client-secret",
        "SSO_GOOGLE_DISCOVERY_URL": "",
        "SSO_GOOGLE_SCOPES": "openid,email",
        "SSO_GOOGLE_PKCE_REQUIRED": "false",
        "SSO_GOOGLE_AUTO_PROVISION_POLICY": "invite_only",
        "SSO_GOOGLE_ALLOWED_DOMAINS": "",
        "SSO_GOOGLE_DEFAULT_ROLE": "member",
    }


def test_build_config_from_env_parses_scopes() -> None:
    env = _base_env()
    config = build_config_from_env(env, provider_key=GOOGLE_PROVIDER_KEY)
    assert config is not None
    assert config.scopes == ["openid", "email"]
    assert config.pkce_required is False


def test_build_config_from_env_parses_id_token_algs() -> None:
    env = _base_env()
    env["SSO_GOOGLE_ID_TOKEN_ALGS"] = "RS256,ES256"
    config = build_config_from_env(env, provider_key=GOOGLE_PROVIDER_KEY)
    assert config is not None
    assert config.allowed_id_token_algs == ["RS256", "ES256"]


def test_build_config_from_env_rejects_template_issuer_defaults() -> None:
    env = _base_env()
    env["SSO_GOOGLE_ISSUER_URL"] = ""
    defaults = {"issuer_url": "https://login.microsoftonline.com/{tenant_id}/v2.0"}
    with pytest.raises(CLIError, match="template placeholders"):
        build_config_from_env(
            env,
            provider_key=GOOGLE_PROVIDER_KEY,
            defaults=defaults,
        )


def test_build_config_from_env_rejects_template_discovery_url() -> None:
    env = _base_env()
    env["SSO_GOOGLE_DISCOVERY_URL"] = "https://{tenant}/.well-known/openid-configuration"
    with pytest.raises(CLIError, match="template placeholders"):
        build_config_from_env(env, provider_key=GOOGLE_PROVIDER_KEY)


def test_build_config_from_env_rejects_global_scope_with_tenant_values() -> None:
    env = _base_env()
    env["SSO_GOOGLE_SCOPE"] = "global"
    env["SSO_GOOGLE_TENANT_ID"] = "tenant-id"
    with pytest.raises(CLIError, match="TENANT_ID"):
        build_config_from_env(env, provider_key=GOOGLE_PROVIDER_KEY)


def test_build_config_from_env_requires_domains() -> None:
    env = _base_env()
    env["SSO_GOOGLE_AUTO_PROVISION_POLICY"] = "domain_allowlist"
    with pytest.raises(CLIError, match="allowed_domains"):
        build_config_from_env(env, provider_key=GOOGLE_PROVIDER_KEY)


def test_build_config_from_env_requires_pkce_for_public_client() -> None:
    env = _base_env()
    env["SSO_GOOGLE_TOKEN_AUTH_METHOD"] = "none"
    env["SSO_GOOGLE_PKCE_REQUIRED"] = "false"
    with pytest.raises(CLIError, match="PKCE"):
        build_config_from_env(env, provider_key=GOOGLE_PROVIDER_KEY)


def test_build_config_from_env_ignores_enabled_flag_when_configured() -> None:
    env = _base_env() | {"SSO_GOOGLE_ENABLED": "false"}
    config = build_config_from_env(
        env,
        provider_key=GOOGLE_PROVIDER_KEY,
        enabled_default=True,
        enforce_enabled_flag=False,
    )
    assert config is not None
    assert config.provider_key == "google"


def test_normalize_provider_key_lowercases() -> None:
    assert normalize_provider_key("Google") == "google"


def test_normalize_provider_key_rejects_invalid() -> None:
    with pytest.raises(CLIError, match="provider_key"):
        normalize_provider_key("bad-key")


def test_normalize_provider_key_rejects_reserved() -> None:
    with pytest.raises(CLIError, match="reserved"):
        normalize_provider_key("custom")


def test_parse_provider_list_dedupes() -> None:
    providers = parse_provider_list("google,azure,google")
    assert providers == ["google", "azure"]


def test_parse_provider_list_rejects_reserved() -> None:
    with pytest.raises(CLIError, match="reserved"):
        parse_provider_list("custom")


def test_resolve_enabled_providers_prefers_list() -> None:
    env = _base_env() | {
        "SSO_PROVIDERS": "azure,google",
        "SSO_AZURE_ENABLED": "false",
    }
    providers = resolve_enabled_providers(env)
    assert providers == ["azure", "google"]


def test_resolve_enabled_providers_requires_list() -> None:
    env = _base_env().copy()
    env.pop("SSO_GOOGLE_ENABLED", None)
    with pytest.raises(CLIError, match="SSO_PROVIDERS"):
        resolve_enabled_providers(env)


def test_resolve_enabled_providers_respects_empty_list() -> None:
    env = _base_env() | {
        "SSO_PROVIDERS": "",
        "SSO_AZURE_ENABLED": "true",
    }
    providers = resolve_enabled_providers(env)
    assert providers == []
