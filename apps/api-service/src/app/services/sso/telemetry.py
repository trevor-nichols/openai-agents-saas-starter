"""SSO event logging helpers."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.observability.logging import log_event


def log_sso_event(
    event: str,
    *,
    result: str,
    reason: str | None = None,
    provider: str | None = None,
    tenant_id: UUID | str | None = None,
    tenant_slug: str | None = None,
    user_id: UUID | str | None = None,
    detail: str | None = None,
) -> None:
    fields: dict[str, Any] = {"result": result}
    if reason:
        fields["reason"] = reason
    if provider:
        fields["provider"] = provider
    if tenant_id:
        fields["tenant_id"] = str(tenant_id)
    if tenant_slug:
        fields["tenant_slug"] = tenant_slug
    if user_id:
        fields["user_id"] = str(user_id)
    if detail:
        fields["detail"] = detail
    log_event(event, **fields)


__all__ = ["log_sso_event"]
