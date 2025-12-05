from __future__ import annotations

from collections.abc import Sequence
from unittest.mock import MagicMock

import pytest

from app.domain.auth import ServiceAccountTokenListResult, ServiceAccountTokenStatus
from app.services.auth.refresh_token_manager import RefreshTokenManager
from app.services.auth.service_account_service import ServiceAccountTokenService


class StubRefreshTokenManager(RefreshTokenManager):
    def __init__(self, result: ServiceAccountTokenListResult) -> None:
        super().__init__(repository=None)
        self._result = result
        self.captured_args: dict[str, object] | None = None

    async def list_tokens(
        self,
        *,
        tenant_ids: Sequence[str] | None,
        include_global: bool,
        account_query: str | None,
        fingerprint: str | None,
        status: ServiceAccountTokenStatus,
        limit: int,
        offset: int,
        require: bool = True,
    ) -> ServiceAccountTokenListResult:
        self.captured_args = {
            "tenant_ids": list(tenant_ids) if tenant_ids is not None else None,
            "include_global": include_global,
            "account_query": account_query,
            "fingerprint": fingerprint,
            "status": status,
            "limit": limit,
            "offset": offset,
            "require": require,
        }
        return self._result


@pytest.mark.asyncio
async def test_list_tokens_forwards_arguments_to_refresh_manager() -> None:
    expected = ServiceAccountTokenListResult(tokens=[], total=0)
    manager = StubRefreshTokenManager(expected)
    service = ServiceAccountTokenService(registry=MagicMock(), refresh_tokens=manager)

    result = await service.list_tokens(
        tenant_ids=["tenant-1"],
        include_global=False,
        account_query="batch",
        fingerprint="runner",
        status=ServiceAccountTokenStatus.ACTIVE,
        limit=10,
        offset=5,
    )

    assert result is expected
    assert manager.captured_args == {
        "tenant_ids": ["tenant-1"],
        "include_global": False,
        "account_query": "batch",
        "fingerprint": "runner",
        "status": ServiceAccountTokenStatus.ACTIVE,
        "limit": 10,
        "offset": 5,
        "require": False,
    }
