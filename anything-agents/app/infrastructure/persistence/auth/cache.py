"""Redis-backed cache for refresh-token lookups."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Protocol

from redis.asyncio import Redis

from app.core.config import Settings
from app.domain.auth import RefreshTokenRecord


class RefreshTokenCache(Protocol):
    async def get(self, account: str, tenant_id: str | None, scope_key: str) -> RefreshTokenRecord | None:
        ...

    async def set(self, record: RefreshTokenRecord) -> None:
        ...

    async def invalidate(self, account: str, tenant_id: str | None, scope_key: str) -> None:
        ...


class NullRefreshTokenCache:
    async def get(self, account: str, tenant_id: str | None, scope_key: str) -> RefreshTokenRecord | None:
        return None

    async def set(self, record: RefreshTokenRecord) -> None:
        return None

    async def invalidate(self, account: str, tenant_id: str | None, scope_key: str) -> None:
        return None


class RedisRefreshTokenCache:
    """Redis cache for refresh tokens, keyed by account/tenant/scope."""

    def __init__(self, client: Redis, *, prefix: str = "auth:refresh") -> None:
        self._client = client
        self._prefix = prefix

    async def get(
        self, account: str, tenant_id: str | None, scope_key: str
    ) -> RefreshTokenRecord | None:
        key = self._key(account, tenant_id, scope_key)
        payload = await self._client.get(key)
        if not payload:
            return None
        data = json.loads(payload)
        expires_at = datetime.fromisoformat(data["expires_at"])
        if expires_at <= datetime.now(timezone.utc):
            await self._client.delete(key)
            return None
        return RefreshTokenRecord(
            token=data["token"],
            jti=data["jti"],
            account=data["account"],
            tenant_id=data.get("tenant_id"),
            scopes=data["scopes"],
            expires_at=expires_at,
            issued_at=datetime.fromisoformat(data["issued_at"]),
            fingerprint=data.get("fingerprint"),
        )

    async def set(self, record: RefreshTokenRecord) -> None:
        ttl = int((record.expires_at - datetime.now(timezone.utc)).total_seconds())
        if ttl <= 0:
            return
        key = self._key(record.account, record.tenant_id, record.scope_key)
        payload = json.dumps(
            {
                "token": record.token,
                "jti": record.jti,
                "account": record.account,
                "tenant_id": record.tenant_id,
                "scopes": record.scopes,
                "expires_at": record.expires_at.isoformat(),
                "issued_at": record.issued_at.isoformat(),
                "fingerprint": record.fingerprint,
            }
        )
        await self._client.set(key, payload, ex=ttl)

    async def invalidate(self, account: str, tenant_id: str | None, scope_key: str) -> None:
        await self._client.delete(self._key(account, tenant_id, scope_key))

    def _key(self, account: str, tenant_id: str | None, scope_key: str) -> str:
        tenant_part = tenant_id or "global"
        return f"{self._prefix}:{account}:{tenant_part}:{scope_key}"


def build_refresh_token_cache(settings: Settings) -> RefreshTokenCache:
    if not settings.redis_url:
        return NullRefreshTokenCache()
    client = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=False)
    return RedisRefreshTokenCache(client)
