from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

from app.core.settings import get_settings
from app.domain.sso import (
    SsoAutoProvisionPolicy,
    SsoProviderConfigUpsert,
    SsoTokenAuthMethod,
)
from app.domain.tenant_roles import TenantRole, normalize_tenant_role
from app.infrastructure.db import dispose_engine
from app.infrastructure.db.engine import init_engine
from app.infrastructure.persistence.auth.sso_repository import (
    get_sso_provider_config_repository,
)
from app.infrastructure.persistence.tenants.account_repository import (
    get_tenant_account_repository,
)
from app.services.sso.config import normalize_provider_key
from app.services.sso.errors import SsoConfigurationError

_DEFAULT_SCOPES = ("openid", "email", "profile")
_ALLOWED_ID_TOKEN_ALGS = {
    "RS256",
    "RS384",
    "RS512",
    "PS256",
    "PS384",
    "PS512",
    "ES256",
    "ES384",
    "ES512",
}


@dataclass(slots=True)
class SeedSsoProviderArgs:
    provider_key: str
    enabled: bool
    tenant_id: UUID | None
    tenant_slug: str | None
    issuer_url: str
    client_id: str
    client_secret: str | None
    clear_client_secret: bool
    discovery_url: str | None
    scopes: list[str]
    pkce_required: bool
    token_auth_method: SsoTokenAuthMethod
    allowed_id_token_algs: list[str]
    auto_provision_policy: SsoAutoProvisionPolicy
    allowed_domains: list[str]
    default_role: TenantRole


async def _resolve_tenant_id(args: SeedSsoProviderArgs) -> UUID | None:
    if args.tenant_id and args.tenant_slug:
        raise RuntimeError("Provide only one of tenant_id or tenant_slug.")
    if args.tenant_id:
        return args.tenant_id
    if not args.tenant_slug:
        return None

    tenant_repo = get_tenant_account_repository(get_settings())
    if tenant_repo is None:
        raise RuntimeError("Tenant repository unavailable; check DATABASE_URL.")
    tenant = await tenant_repo.get_by_slug(args.tenant_slug)
    if tenant is None:
        raise RuntimeError(f"Tenant slug not found: {args.tenant_slug}")
    return tenant.id


async def _seed_provider(args: SeedSsoProviderArgs) -> dict[str, object]:
    await init_engine(run_migrations=False)
    try:
        settings = get_settings()
        repo = get_sso_provider_config_repository(settings)
        if repo is None:
            raise RuntimeError("SSO provider repository unavailable; check DATABASE_URL.")

        tenant_id = await _resolve_tenant_id(args)
        existing = await repo.fetch(tenant_id=tenant_id, provider_key=args.provider_key)
        result = "created" if existing is None else "updated"

        if (
            args.token_auth_method
            in {
                SsoTokenAuthMethod.CLIENT_SECRET_BASIC,
                SsoTokenAuthMethod.CLIENT_SECRET_POST,
            }
            and not args.clear_client_secret
            and args.client_secret is None
            and (existing is None or not existing.client_secret)
        ):
            raise RuntimeError("client_secret is required for the selected token auth method.")

        payload = SsoProviderConfigUpsert(
            tenant_id=tenant_id,
            provider_key=args.provider_key,
            enabled=args.enabled,
            issuer_url=args.issuer_url,
            client_id=args.client_id,
            client_secret=args.client_secret,
            clear_client_secret=args.clear_client_secret,
            discovery_url=args.discovery_url,
            scopes=args.scopes,
            pkce_required=args.pkce_required,
            token_endpoint_auth_method=args.token_auth_method,
            allowed_id_token_algs=args.allowed_id_token_algs,
            auto_provision_policy=args.auto_provision_policy,
            allowed_domains=args.allowed_domains,
            default_role=args.default_role,
        )
        saved = await repo.upsert(payload)

        return {
            "result": result,
            "provider_key": saved.provider_key,
            "tenant_id": str(saved.tenant_id) if saved.tenant_id else None,
            "tenant_slug": args.tenant_slug,
            "config_id": str(saved.id),
            "enabled": bool(saved.enabled),
            "issuer_url": saved.issuer_url,
            "client_id": saved.client_id,
            "discovery_url": saved.discovery_url,
            "scopes": list(saved.scopes),
            "pkce_required": bool(saved.pkce_required),
            "token_auth_method": saved.token_endpoint_auth_method.value,
            "allowed_id_token_algs": list(saved.allowed_id_token_algs),
            "auto_provision_policy": saved.auto_provision_policy.value,
            "allowed_domains": list(saved.allowed_domains),
            "default_role": saved.default_role.value,
        }
    finally:
        await dispose_engine()


def _parse_list(value: str | None) -> list[str]:
    if not value:
        return []
    raw = value.strip()
    if not raw:
        return []
    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON list: {exc}") from exc
        if not isinstance(parsed, list):
            raise RuntimeError("Expected a JSON list.")
        return [str(item).strip() for item in parsed if str(item).strip()]
    if "," in raw:
        return [item.strip() for item in raw.split(",") if item.strip()]
    return [item.strip() for item in raw.split() if item.strip()]


def _parse_scopes(raw: str | None) -> list[str]:
    scopes = _parse_list(raw)
    if scopes:
        return scopes
    return list(_DEFAULT_SCOPES)


def _parse_id_token_algs(raw: str | None) -> list[str]:
    algs = _parse_list(raw)
    if not algs:
        return []
    normalized = [str(item).strip().upper() for item in algs if str(item).strip()]
    invalid = [alg for alg in normalized if alg not in _ALLOWED_ID_TOKEN_ALGS]
    if invalid:
        raise RuntimeError(
            "id_token_algs must be one of "
            f"{', '.join(sorted(_ALLOWED_ID_TOKEN_ALGS))}."
        )
    return normalized


def _parse_token_auth_method(raw: str | None) -> SsoTokenAuthMethod:
    value = (raw or SsoTokenAuthMethod.CLIENT_SECRET_POST.value).strip().lower()
    try:
        return SsoTokenAuthMethod(value)
    except ValueError as exc:
        raise RuntimeError(
            "token_auth_method must be one of "
            f"{', '.join(method.value for method in SsoTokenAuthMethod)}."
        ) from exc


def _parse_policy(raw: str | None) -> SsoAutoProvisionPolicy:
    value = (raw or "invite_only").strip().lower()
    try:
        return SsoAutoProvisionPolicy(value)
    except ValueError as exc:
        raise RuntimeError(
            "auto_provision_policy must be one of disabled, invite_only, domain_allowlist."
        ) from exc


def _parse_role(raw: str | None) -> TenantRole:
    role = normalize_tenant_role(raw or "member")
    if role is None:
        raise RuntimeError("default_role must be one of owner, admin, member, viewer.")
    return role


def _parse_uuid(raw: str | None) -> UUID | None:
    if not raw:
        return None
    try:
        return UUID(str(raw))
    except ValueError as exc:
        raise RuntimeError(f"Invalid UUID: {raw}") from exc


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed or update an SSO provider config.")
    parser.add_argument("--provider", default="google")
    parser.add_argument("--tenant-id")
    parser.add_argument("--tenant-slug")
    parser.add_argument("--issuer-url", required=True)
    parser.add_argument("--client-id", required=True)
    secret_group = parser.add_mutually_exclusive_group()
    secret_group.add_argument("--client-secret")
    secret_group.add_argument(
        "--clear-client-secret",
        action="store_true",
        help="Clear the stored client secret.",
    )
    parser.add_argument("--discovery-url")
    parser.add_argument("--scopes", help="Comma-separated or JSON list of scopes")
    parser.add_argument(
        "--token-auth-method",
        choices=[method.value for method in SsoTokenAuthMethod],
        default=SsoTokenAuthMethod.CLIENT_SECRET_POST.value,
    )
    parser.add_argument(
        "--id-token-algs",
        help="Comma-separated or JSON list of allowed ID token signing algorithms",
    )
    parser.add_argument("--allowed-domains", help="Comma-separated or JSON list of domains")
    parser.add_argument(
        "--auto-provision-policy",
        default="invite_only",
        choices=[policy.value for policy in SsoAutoProvisionPolicy],
    )
    parser.add_argument(
        "--default-role",
        default="member",
        choices=[role.value for role in TenantRole],
    )

    enabled_group = parser.add_mutually_exclusive_group()
    enabled_group.add_argument("--enable", dest="enabled", action="store_true")
    enabled_group.add_argument("--disable", dest="enabled", action="store_false")

    pkce_group = parser.add_mutually_exclusive_group()
    pkce_group.add_argument("--pkce-required", dest="pkce_required", action="store_true")
    pkce_group.add_argument("--no-pkce", dest="pkce_required", action="store_false")

    return parser


def _normalize_args(ns: argparse.Namespace) -> SeedSsoProviderArgs:
    enabled = True if ns.enabled is None else bool(ns.enabled)
    pkce_required = True if ns.pkce_required is None else bool(ns.pkce_required)
    clear_client_secret = bool(getattr(ns, "clear_client_secret", False))

    raw_provider = str(ns.provider or "").strip()
    try:
        provider_key = normalize_provider_key(raw_provider)
    except SsoConfigurationError as exc:
        raise RuntimeError(str(exc)) from exc
    if provider_key == "custom":
        print(
            "WARN: provider_key 'custom' is reserved for console presets; "
            "use a distinct provider key for backend seeding.",
            file=sys.stderr,
        )

    issuer_url = str(ns.issuer_url or "").strip()
    client_id = str(ns.client_id or "").strip()
    client_secret = str(ns.client_secret or "").strip()
    token_auth_method = _parse_token_auth_method(ns.token_auth_method)
    if token_auth_method == SsoTokenAuthMethod.NONE and not pkce_required:
        raise RuntimeError("pkce_required must be true when token_auth_method is none.")
    if not issuer_url:
        raise RuntimeError("issuer_url is required.")
    if not client_id:
        raise RuntimeError("client_id is required.")
    if clear_client_secret and token_auth_method in {
        SsoTokenAuthMethod.CLIENT_SECRET_BASIC,
        SsoTokenAuthMethod.CLIENT_SECRET_POST,
    }:
        raise RuntimeError(
            "Cannot clear client_secret for the selected token auth method. "
            "Provide a new secret or change token_auth_method."
        )
    if not client_secret:
        client_secret = None

    policy = _parse_policy(ns.auto_provision_policy)
    allowed_domains = _parse_list(ns.allowed_domains)
    if policy == SsoAutoProvisionPolicy.DOMAIN_ALLOWLIST and not allowed_domains:
        raise RuntimeError("allowed_domains is required for domain_allowlist policy.")

    return SeedSsoProviderArgs(
        provider_key=provider_key,
        enabled=enabled,
        tenant_id=_parse_uuid(ns.tenant_id),
        tenant_slug=str(ns.tenant_slug).strip() if ns.tenant_slug else None,
        issuer_url=issuer_url,
        client_id=client_id,
        client_secret=client_secret,
        clear_client_secret=clear_client_secret,
        discovery_url=str(ns.discovery_url).strip() if ns.discovery_url else None,
        scopes=_parse_scopes(ns.scopes),
        pkce_required=pkce_required,
        token_auth_method=token_auth_method,
        allowed_id_token_algs=_parse_id_token_algs(ns.id_token_algs),
        auto_provision_policy=policy,
        allowed_domains=allowed_domains,
        default_role=_parse_role(ns.default_role),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    ns = parser.parse_args(list(argv) if argv is not None else None)

    # Ensure script output is JSON-only for callers.
    os.environ["DATABASE_ECHO"] = "false"

    try:
        args = _normalize_args(ns)
        payload = asyncio.run(_seed_provider(args))
    except Exception as exc:  # pragma: no cover - runtime errors
        error_payload = {"result": "error", "detail": str(exc)}
        print(json.dumps(error_payload))
        return 1

    print(json.dumps(payload))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
