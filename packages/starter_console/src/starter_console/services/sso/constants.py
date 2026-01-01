from __future__ import annotations

GOOGLE_PROVIDER_KEY = "google"
GOOGLE_ISSUER_URL = "https://accounts.google.com"
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

DEFAULT_SCOPES = ("openid", "email", "profile")
DEFAULT_AUTO_PROVISION_POLICY = "invite_only"
DEFAULT_ROLE = "member"
DEFAULT_SCOPE_MODE = "global"
DEFAULT_TOKEN_AUTH_METHOD = "client_secret_post"

AUTO_PROVISION_POLICIES = ("disabled", "invite_only", "domain_allowlist")
ROLE_CHOICES = ("owner", "admin", "member", "viewer")
SCOPE_MODE_CHOICES = ("global", "tenant")
TOKEN_AUTH_METHOD_CHOICES = (
    "client_secret_post",
    "client_secret_basic",
    "none",
)
ID_TOKEN_ALG_CHOICES = (
    "RS256",
    "RS384",
    "RS512",
    "PS256",
    "PS384",
    "PS512",
    "ES256",
    "ES384",
    "ES512",
)

__all__ = [
    "AUTO_PROVISION_POLICIES",
    "DEFAULT_AUTO_PROVISION_POLICY",
    "DEFAULT_ROLE",
    "DEFAULT_SCOPES",
    "DEFAULT_SCOPE_MODE",
    "DEFAULT_TOKEN_AUTH_METHOD",
    "GOOGLE_DISCOVERY_URL",
    "GOOGLE_ISSUER_URL",
    "GOOGLE_PROVIDER_KEY",
    "ID_TOKEN_ALG_CHOICES",
    "ROLE_CHOICES",
    "SCOPE_MODE_CHOICES",
    "TOKEN_AUTH_METHOD_CHOICES",
]
