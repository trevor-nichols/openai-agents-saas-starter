"""Redis-backed SSO state/nonce/PKCE storage."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Protocol, cast

from app.core.settings import Settings, get_settings
from app.infrastructure.redis.factory import get_redis_factory
from app.infrastructure.redis_types import RedisBytesClient


@dataclass(slots=True)
class SsoStatePayload:
    tenant_id: str | None
    provider_key: str
    pkce_verifier: str | None
    nonce: str
    redirect_uri: str
    scopes: list[str]


class SsoStateStore(Protocol):
    async def set_state(self, state: str, payload: SsoStatePayload) -> None: ...

    async def consume_state(self, state: str) -> SsoStatePayload | None: ...


class RedisSsoStateStore(SsoStateStore):
    def __init__(
        self,
        client: RedisBytesClient,
        *,
        ttl_seconds: int,
        prefix: str = "sso:state",
    ) -> None:
        self._client = client
        self._ttl_seconds = max(ttl_seconds, 30)
        self._prefix = prefix

    async def set_state(self, state: str, payload: SsoStatePayload) -> None:
        key = self._key(state)
        encoded = json.dumps(asdict(payload)).encode("utf-8")
        await self._client.set(key, encoded, ex=self._ttl_seconds)

    async def consume_state(self, state: str) -> SsoStatePayload | None:
        key = self._key(state)
        raw = await cast(Any, self._client).eval(
            "local v = redis.call('GET', KEYS[1]);"
            "if v then redis.call('DEL', KEYS[1]); end;"
            "return v;",
            1,
            key,
        )
        if raw is None:
            return None
        if isinstance(raw, memoryview):
            raw = raw.tobytes()
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        if not isinstance(payload, dict):
            return None
        provider_key = payload.get("provider_key")
        nonce = payload.get("nonce")
        redirect_uri = payload.get("redirect_uri")
        scopes_raw = payload.get("scopes")
        if (
            not isinstance(provider_key, str)
            or not provider_key.strip()
            or not isinstance(nonce, str)
            or not nonce.strip()
            or not isinstance(redirect_uri, str)
            or not redirect_uri.strip()
        ):
            return None
        if scopes_raw is None:
            scopes = []
        elif isinstance(scopes_raw, list):
            scopes = [str(item).strip() for item in scopes_raw if str(item).strip()]
        else:
            return None
        tenant_id = payload.get("tenant_id")
        if tenant_id is not None and not isinstance(tenant_id, str):
            return None
        tenant_id = tenant_id.strip() if isinstance(tenant_id, str) else None
        if tenant_id == "":
            tenant_id = None
        pkce_verifier = payload.get("pkce_verifier")
        if pkce_verifier is not None and not isinstance(pkce_verifier, str):
            return None
        if isinstance(pkce_verifier, str) and not pkce_verifier.strip():
            pkce_verifier = None
        return SsoStatePayload(
            tenant_id=cast(str | None, tenant_id),
            provider_key=provider_key.strip(),
            pkce_verifier=cast(str | None, pkce_verifier),
            nonce=nonce,
            redirect_uri=redirect_uri,
            scopes=scopes,
        )

    def _key(self, state: str) -> str:
        return f"{self._prefix}:{state}"


def build_sso_state_store(settings: Settings | None = None) -> SsoStateStore:
    resolved = settings or get_settings()
    redis_url = resolved.resolve_auth_cache_redis_url()
    if not redis_url:
        raise RuntimeError("AUTH_CACHE_REDIS_URL (or REDIS_URL) is required for SSO state.")
    client = cast(RedisBytesClient, get_redis_factory(resolved).get_client("auth_cache"))
    ttl_seconds = int(resolved.sso_state_ttl_minutes * 60)
    return RedisSsoStateStore(client, ttl_seconds=ttl_seconds)


__all__ = ["SsoStatePayload", "SsoStateStore", "RedisSsoStateStore", "build_sso_state_store"]
