from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.api.dependencies.service_accounts import (
    ServiceAccountActor,
    ServiceAccountActorType,
)
from app.api.v1.auth.routes_service_account_tokens import _resolve_scope


def test_scope_enforces_tenant_admin_boundary() -> None:
    actor = ServiceAccountActor(ServiceAccountActorType.TENANT_ADMIN, "tenant-1", user={})
    tenant_ids, include_global = _resolve_scope(actor, None, True)

    assert tenant_ids == ["tenant-1"]
    assert include_global is False

    with pytest.raises(HTTPException):
        _resolve_scope(actor, "tenant-2", False)


def test_scope_allows_operator_access() -> None:
    actor = ServiceAccountActor(
        ServiceAccountActorType.PLATFORM_OPERATOR,
        None,
        user={},
        reason="audit",
    )

    tenant_ids, include_global = _resolve_scope(actor, "tenant-3", True)

    assert tenant_ids == ["tenant-3"]
    assert include_global is True

    tenant_ids_all, include_global_all = _resolve_scope(actor, None, False)
    assert tenant_ids_all is None
    assert include_global_all is False
