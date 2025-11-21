from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.domain.auth import SessionLocation, UserSessionRepository
from app.services.auth.session_store import SessionStore
from app.services.geoip_service import GeoIPService


@pytest.mark.asyncio
async def test_session_store_enriches_location(monkeypatch: pytest.MonkeyPatch) -> None:
    upsert_mock = AsyncMock()
    repository = cast(
        UserSessionRepository,
        SimpleNamespace(
            upsert_session=upsert_mock,
            list_sessions=AsyncMock(),
            get_session=AsyncMock(),
            mark_session_revoked=AsyncMock(),
            mark_session_revoked_by_jti=AsyncMock(),
            revoke_all_for_user=AsyncMock(),
        ),
    )
    lookup_mock = AsyncMock(
        return_value=SessionLocation(city="Austin", region="Texas", country="US")
    )
    geoip = cast(GeoIPService, SimpleNamespace(lookup=lookup_mock))
    store = SessionStore(repository=repository, geoip_service=geoip)
    await store.upsert(
        session_id=uuid4(),
        user_id=uuid4(),
        tenant_id=uuid4(),
        refresh_jti="refresh",
        fingerprint=None,
        ip_address="8.8.8.8",
        user_agent="pytest",
        occurred_at=datetime.now(UTC),
    )
    lookup_mock.assert_awaited_once_with("8.8.8.8")
    call = upsert_mock.await_args
    assert call is not None
    assert call.kwargs["location"] == SessionLocation(
        city="Austin", region="Texas", country="US"
    )
