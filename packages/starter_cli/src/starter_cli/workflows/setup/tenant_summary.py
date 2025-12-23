from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine


@dataclass(slots=True)
class TenantSummary:
    tenant_id: str
    slug: str
    name: str | None
    created_at: str | None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "tenant_id": self.tenant_id,
            "slug": self.slug,
            "name": self.name,
            "created_at": self.created_at,
        }


_TENANT_QUERY = text(
    """
    SELECT id, slug, name, created_at
    FROM tenant_accounts
    WHERE slug = :slug
    ORDER BY created_at ASC
    LIMIT 1
    """
)

_TENANT_FALLBACK_QUERY = text(
    """
    SELECT id, slug, name, created_at
    FROM tenant_accounts
    ORDER BY created_at ASC
    LIMIT 1
    """
)


def capture_tenant_summary(context) -> TenantSummary | None:
    """Attempt to populate the wizard context with a tenant summary."""

    database_url = context.current("DATABASE_URL")
    if not database_url:
        context.console.warn(
            "DATABASE_URL is not set; skipping tenant lookup.",
            topic="tenant",
        )
        return None

    preferred_slug = context.current("TENANT_DEFAULT_SLUG") or None
    try:
        summary = asyncio.run(_lookup_tenant(database_url, preferred_slug))
    except Exception as exc:  # pragma: no cover - defensive fallback
        context.console.warn(f"Unable to query tenant_accounts ({exc}).", topic="tenant")
        return None

    if summary is None:
        context.console.warn(
            "No tenant records found. Run `python -m starter_cli.app users seed` "
            "to provision the first tenant.",
            topic="tenant",
        )
        return None

    context.tenant_summary = summary
    if preferred_slug and summary.slug != preferred_slug:
        context.console.info(
            f"Tenant slug '{preferred_slug}' not found; showing earliest tenant instead.",
            topic="tenant",
        )

    context.console.success(
        f"Tenant '{summary.slug}' UUID: {summary.tenant_id}",
        topic="tenant",
    )
    context.console.info(
        "Copy this UUID into operator runbooks/CI secrets so API clients can set the tenant scope.",
        topic="tenant",
    )
    return summary


async def _lookup_tenant(database_url: str, preferred_slug: str | None) -> TenantSummary | None:
    engine = create_async_engine(database_url)
    try:
        async with engine.connect() as conn:
            row = None
            if preferred_slug is not None:
                row = await _fetch_row(conn, _TENANT_QUERY, slug=preferred_slug)
            if row is None:
                row = await _fetch_row(conn, _TENANT_FALLBACK_QUERY)
    finally:
        await engine.dispose()

    if row is None:
        return None

    mapping = row._mapping if hasattr(row, "_mapping") else row
    created_at = mapping.get("created_at")
    if isinstance(created_at, datetime):
        created_at_value = created_at.isoformat()
    elif created_at is None:
        created_at_value = None
    else:
        created_at_value = str(created_at)
    return TenantSummary(
        tenant_id=str(mapping.get("id")),
        slug=str(mapping.get("slug")),
        name=str(mapping.get("name")) if mapping.get("name") is not None else None,
        created_at=created_at_value,
    )


async def _fetch_row(connection, query, **params: Any):
    try:
        result = await connection.execute(query, params)
    except SQLAlchemyError as exc:
        raise RuntimeError(str(exc)) from exc
    return result.first()
