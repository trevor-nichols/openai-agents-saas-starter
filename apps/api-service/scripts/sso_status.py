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
from app.infrastructure.db import dispose_engine
from app.infrastructure.db.engine import init_engine
from app.infrastructure.persistence.auth.sso_repository import (
    get_sso_provider_config_repository,
)
from app.infrastructure.persistence.tenants.account_repository import (
    get_tenant_account_repository,
)


@dataclass(slots=True)
class SsoStatusArgs:
    provider_key: str
    tenant_id: UUID | None
    tenant_slug: str | None
    include_global: bool


async def _resolve_tenant_id(args: SsoStatusArgs) -> UUID | None:
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


async def _load_status(args: SsoStatusArgs) -> dict[str, object]:
    await init_engine(run_migrations=False)
    try:
        settings = get_settings()
        repo = get_sso_provider_config_repository(settings)
        if repo is None:
            raise RuntimeError("SSO provider repository unavailable; check DATABASE_URL.")

        tenant_id = await _resolve_tenant_id(args)
        config = None
        source = "none"

        if tenant_id is not None or args.tenant_slug:
            config = await repo.fetch(tenant_id=tenant_id, provider_key=args.provider_key)
            if config is not None:
                source = "tenant"

        if config is None and args.include_global:
            config = await repo.fetch(tenant_id=None, provider_key=args.provider_key)
            if config is not None:
                source = "global"

        if config is None:
            return {
                "result": "not_configured",
                "provider_key": args.provider_key,
                "tenant_id": str(tenant_id) if tenant_id else None,
                "tenant_slug": args.tenant_slug,
                "config_source": None,
            }

        return {
            "result": "ok",
            "provider_key": config.provider_key,
            "tenant_id": str(config.tenant_id) if config.tenant_id else None,
            "tenant_slug": args.tenant_slug,
            "config_source": source,
            "enabled": bool(config.enabled),
            "issuer_url": config.issuer_url,
            "discovery_url": config.discovery_url,
            "scopes": list(config.scopes),
            "pkce_required": bool(config.pkce_required),
            "token_auth_method": config.token_endpoint_auth_method.value,
            "allowed_id_token_algs": list(config.allowed_id_token_algs),
            "auto_provision_policy": config.auto_provision_policy.value,
            "allowed_domains_count": len(config.allowed_domains),
            "default_role": config.default_role.value,
            "updated_at": config.updated_at.isoformat(),
        }
    finally:
        await dispose_engine()


def _parse_uuid(raw: str | None) -> UUID | None:
    if not raw:
        return None
    try:
        return UUID(str(raw))
    except ValueError as exc:
        raise RuntimeError(f"Invalid UUID: {raw}") from exc


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check SSO provider configuration status.")
    parser.add_argument("--provider", default="google")
    parser.add_argument("--tenant-id")
    parser.add_argument("--tenant-slug")
    parser.add_argument(
        "--include-global",
        dest="include_global",
        action="store_true",
        default=True,
        help="Allow global fallback when tenant config is missing.",
    )
    parser.add_argument(
        "--no-include-global",
        dest="include_global",
        action="store_false",
    )
    return parser


def _normalize_args(ns: argparse.Namespace) -> SsoStatusArgs:
    provider_key = str(ns.provider or "").strip().lower()
    if not provider_key:
        raise RuntimeError("provider is required.")

    return SsoStatusArgs(
        provider_key=provider_key,
        tenant_id=_parse_uuid(ns.tenant_id),
        tenant_slug=str(ns.tenant_slug).strip() if ns.tenant_slug else None,
        include_global=bool(ns.include_global),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    ns = parser.parse_args(list(argv) if argv is not None else None)

    # Ensure script output is JSON-only for callers.
    os.environ["DATABASE_ECHO"] = "false"

    try:
        args = _normalize_args(ns)
        payload = asyncio.run(_load_status(args))
    except Exception as exc:  # pragma: no cover - runtime errors
        error_payload = {"result": "error", "detail": str(exc)}
        print(json.dumps(error_payload))
        return 1

    print(json.dumps(payload))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
