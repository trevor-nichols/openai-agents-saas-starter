"""Redis-backed email verification token store."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Final, cast
from uuid import UUID

from app.core.config import Settings, get_settings
from app.domain.email_verification import (
    EmailVerificationTokenRecord,
    EmailVerificationTokenStore,
)
from app.infrastructure.redis.factory import get_redis_factory
from app.infrastructure.redis_types import RedisStrClient


class RedisEmailVerificationTokenStore(EmailVerificationTokenStore):
    def __init__(self, client: RedisStrClient, *, prefix: str = "auth:emailverify") -> None:
        self._client = client
        self._prefix = prefix.rstrip(":")

    async def save(self, record: EmailVerificationTokenRecord, *, ttl_seconds: int) -> None:
        payload = json.dumps(
            {
                "token_id": record.token_id,
                "user_id": str(record.user_id),
                "email": record.email,
                "hashed_secret": record.hashed_secret,
                "created_at": record.created_at.isoformat(),
                "expires_at": record.expires_at.isoformat(),
                "fingerprint": record.fingerprint,
            }
        )
        await self._client.set(self._key(record.token_id), payload, ex=ttl_seconds)

    async def get(self, token_id: str) -> EmailVerificationTokenRecord | None:
        raw = await self._client.get(self._key(token_id))
        if not raw:
            return None
        data = json.loads(raw)
        return EmailVerificationTokenRecord(
            token_id=data["token_id"],
            user_id=UUID(data["user_id"]),
            email=data["email"],
            hashed_secret=data["hashed_secret"],
            created_at=datetime.fromisoformat(data["created_at"]).astimezone(UTC),
            expires_at=datetime.fromisoformat(data["expires_at"]).astimezone(UTC),
            fingerprint=data.get("fingerprint"),
        )

    async def delete(self, token_id: str) -> None:
        await self._client.delete(self._key(token_id))

    def _key(self, token_id: str) -> str:
        return f"{self._prefix}:{token_id}"


_STORE_CACHE: dict[str, EmailVerificationTokenStore] = {}


def get_email_verification_token_store(
    settings: Settings | None = None,
) -> EmailVerificationTokenStore:
    settings = settings or get_settings()
    redis_url = settings.resolve_security_token_redis_url()
    if not redis_url:
        raise RuntimeError(
            "SECURITY_TOKEN_REDIS_URL (or REDIS_URL) is required for email verification tokens."
        )
    cached = _STORE_CACHE.get(redis_url)
    if cached:
        return cached
    client = cast(
        RedisStrClient,
        get_redis_factory(settings).get_client("security_tokens", decode_responses=True),
    )
    store = RedisEmailVerificationTokenStore(client)
    _STORE_CACHE[redis_url] = store
    return store


__all__: Final = [
    "RedisEmailVerificationTokenStore",
    "get_email_verification_token_store",
]
